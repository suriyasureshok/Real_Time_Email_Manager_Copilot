import imaplib
import email
from email import message
import asyncio
from kafka import KafkaProducer
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..config.settings import EmailKafkaConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)

class EmailProducer:
    def __init__(self, config: Optional[EmailKafkaConfig] = None, poll_interval: int = 1200):
        """
        Initialize the EmailProducer with Kafka and email server configurations.
        """
        self.config = config or EmailKafkaConfig()
        self.poll_interval = poll_interval  # Use the provided poll_interval
        self.last_poll_time = None  # Track when we last polled for emails
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=5,
                linger_ms=10,
                batch_size=32768,
            )
            logger.info("Kafka Producer initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            raise e
        
        self.imap = None  # IMAP connection will be established later
    async def _connect_to_email_server(self):
        """
        Connect to the IMAP email server.
        """
        def _sync_connect():
            imap = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
            
            # Check if we have valid credentials
            if not self.config.email_user or not self.config.email_password:
                raise ValueError("Email credentials not provided")
            
            login_result = imap.login(self.config.email_user, self.config.email_password)
            if login_result[0] != 'OK':
                raise Exception(f"Login failed: {login_result[1]}")
                
            imap.select('INBOX')
            logger.info("Successfully connected to email server and selected INBOX.")
            return imap
            
        try:
            loop = asyncio.get_event_loop()
            self.imap = await loop.run_in_executor(None, _sync_connect)
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            if hasattr(self, 'imap') and self.imap:
                try:
                    await loop.run_in_executor(None, self.imap.logout)
                except:
                    pass
                self.imap = None
            raise
        
    async def fetch_unseen_emails(self) -> List[Dict]:
        """
        Fetch unseen emails from the email server.
        Returns:
            >>> list of email data dictionaries.
        """
        def _sync_fetch():
            if not hasattr(self, 'imap') or self.imap is None:
                logger.warning("No IMAP connection available")
                return []
            
            # Determine search window
            current_time = datetime.now()
            if self.last_poll_time is None:
                since_time = current_time - timedelta(seconds=self.poll_interval)
                logger.info(f"First poll - searching for emails since {since_time}")
            else:
                since_time = self.last_poll_time
                logger.info(f"Searching for emails since last poll at {since_time}")
            
            # Format IMAP date for search criteria (standard imaplib format)
            since_date_str = since_time.strftime("%d-%b-%Y")
            search_criteria = f'UNSEEN SINCE {since_date_str}'
            logger.debug(f"Using search criteria: {search_criteria}")
            
            # Perform search using standard imaplib
            status, data = self.imap.search(None, search_criteria)
            if status != 'OK' or not data or not data[0]:
                logger.info("No unseen emails found.")
                return []
            
            # Extract email IDs from search result
            email_ids = data[0].decode().split()
            logger.info(f"Found {len(email_ids)} unseen emails within poll interval.")
            
            emails = []
            for email_id in email_ids:
                logger.debug(f"Fetching email ID: {email_id}")
                
                # Fetch email using standard imaplib
                status, msg_data = self.imap.fetch(email_id, '(RFC822)')
                if status != 'OK' or not msg_data:
                    logger.warning(f"Failed to fetch email ID {email_id}")
                    continue
                
                # msg_data is a list of tuples: [(b'1 (RFC822 {size}', raw_email_bytes), b')']
                raw_email = msg_data[0][1]
                try:
                    # Parse the email message from bytes
                    msg = email.message_from_bytes(raw_email)
                    email_data = {
                        'id': email_id,
                        'from': msg.get('From'),
                        'to': msg.get('To'),
                        'subject': msg.get('Subject'),
                        'date': msg.get('Date'),
                        'body': self._get_email_body(msg),
                    }
                    emails.append(email_data)
                    logger.debug(f"Fetched email: {email_data['subject']} from {email_data['from']}")

                except Exception as e:
                    logger.error(f"Error parsing email {email_id}: {e}")
            
            return emails
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _sync_fetch)
        except Exception as e:
            logger.error(f"Error fetching unseen emails: {e}")
            return []
        
    def _get_email_body(self, msg: message.Message) -> str:
        """
        Extract the body from the email message.
        Args:
            msg: The email message object.
        Returns:
            The plain text body of the email.
        """
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return ""
    async def send_email_to_kafka(self, email_data: Dict):
        """
        Send the email data to the Kafka topic.
        Args:
            email_data: The email data dictionary.
        """
        def _sync_send():
            future = self.producer.send(self.config.kafka_topic, value=email_data)
            result = future.get(timeout=10)
            return result
            
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _sync_send)
            logger.info(f"Sent email ID {email_data['id']} to Kafka topic {self.config.kafka_topic}")
        except Exception as e:
            logger.error(f"Failed to send email ID {email_data['id']} to Kafka: {e}")

    async def run(self):
        """
        Main loop to fetch unseen emails and send them to Kafka at regular intervals.
        """
        # Try to connect to email server first
        logger.debug("Starting EmailProducer run loop")
        try:
            logger.debug("Attempting to connect to email server")
            await self._connect_to_email_server()
            logger.info("Connected to email server successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            logger.info("Will continue without email connection - Kafka producer is still available")
        
        while True:
            try:
                # Update the last poll time before fetching emails
                poll_start_time = datetime.now()
                
                emails = await self.fetch_unseen_emails()
                for email_data in emails:
                    await self.send_email_to_kafka(email_data)
                
                # Update last poll time after successful fetch
                self.last_poll_time = poll_start_time
                logger.debug(f"Updated last poll time to {self.last_poll_time}")
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            logger.info(f"Sleeping for {self.poll_interval} seconds before next poll.")
            await asyncio.sleep(self.poll_interval)

    async def close(self):
        """
        Close the IMAP connection and Kafka producer.
        """
        def _sync_cleanup():
            if self.imap:
                self.imap.logout()
                logger.info("Logged out from email server.")
            if self.producer:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed.")
                
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _sync_cleanup)
        except Exception as e:
            logger.error(f"Error closing resources: {e}")