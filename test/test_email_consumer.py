from src.data_consumers.email_consumer import EmailConsumer
import asyncio

if __name__ == "__main__":
    consumer = EmailConsumer()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(consumer.consume_emails())
    except KeyboardInterrupt:
        print("Shutting down email consumer...")