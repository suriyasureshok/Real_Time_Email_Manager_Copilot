from dataclasses import dataclass, field
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file if present

@dataclass
class EmailKafkaConfig:
    """
    Configuration for the Email Kafka integration.
    """
    kafka_bootstrap_servers: List[str] = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    )
    kafka_topic: str = os.getenv("EMAIL_TOPIC", "emails-topic")
    imap_server: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    imap_port: int = int(os.getenv("IMAP_PORT", 993))
    email_user: str = os.getenv("EMAIL_USER")
    email_password: str = os.getenv("EMAIL_PASS")

