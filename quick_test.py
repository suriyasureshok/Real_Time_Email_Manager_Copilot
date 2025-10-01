import sys
sys.path.append('c:/Users/SURIYA/Desktop/ML Projects/Real_time_Data_Streaming_Copilot')

try:
    from src.data_producers.email_producer import EmailProducer
    print("✅ Import successful")
    
    # Quick method check
    import inspect
    methods = ['run', 'fetch_unseen_emails', 'send_email_to_kafka', 'close']
    for method in methods:
        func = getattr(EmailProducer, method)
        is_async = inspect.iscoroutinefunction(func)
        print(f"{method}: {'async' if is_async else 'sync'}")
        
except Exception as e:
    print(f"❌ Error: {e}")