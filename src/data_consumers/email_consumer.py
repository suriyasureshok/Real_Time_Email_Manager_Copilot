from kafka import KafkaConsumer
import json
import asyncio

from ..agents.master_agent import MasterAgent
from ..utils.logger import get_logger
from ..config.settings import EmailKafkaConfig

logger = get_logger(__name__)

class EmailConsumer:
    def __init__(self, config: EmailKafkaConfig = None):
        """
        Initialize the EmailConsumer with Kafka configuration.
        """
        self.config = config or EmailKafkaConfig()
        
        try:
            self.consumer = KafkaConsumer(
                self.config.kafka_topic,
                bootstrap_servers=self.config.kafka_bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='email-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info("Kafka Consumer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Consumer: {e}")
            raise e

    async def consume_emails(self):
        """
        Consume emails from the Kafka topic and process them.
        """
        def _consume_sync():
            """Synchronous consumer loop that runs in executor"""
            try:
                logger.info("Starting to consume emails...")
                for message in self.consumer:
                    logger.debug(f"Received message: {message}")
                    email_data = message.value
                    logger.info(f"Consumed email ID {email_data['id']} from Kafka topic {self.config.kafka_topic}")
                    # Process the email data as needed
                    # Note: We can't call async process_email from sync context
                    # So we'll handle processing here
                    self._process_email_sync(email_data)
            except Exception as e:
                logger.error(f"Error while consuming emails: {e}")
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _consume_sync)
        except Exception as e:
            logger.error(f"Error in async consumer: {e}")

    def _process_email_sync(self, email_data):
        """
        Synchronous email processing for use in executor.
        Args:
            email_data (dict): The email data dictionary.
        """
        logger.debug(f"Processing email: {email_data}")
        master = MasterAgent()
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(master.run(email_data['body']))
        logger.info(f"MasterAgent response: {response}")
