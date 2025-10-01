import os
# Enable debug logging to see detailed email processing
os.environ['LOG_LEVEL'] = 'DEBUG'

from src.data_producers.email_producer import EmailProducer
from src.config.settings import EmailKafkaConfig
import asyncio

if __name__ == "__main__":
    config = EmailKafkaConfig()
    email_producer = EmailProducer(config=config, poll_interval=3600)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(email_producer.run())
    except KeyboardInterrupt:
        print("Shutting down email producer...")
        loop.run_until_complete(email_producer.close())