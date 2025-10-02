from ..agents.storage_agent import StorageAgent
from ..agents.classification_agent import ClassificationAgent
from ..agents.response_agent import ResponseAgent

class MasterAgent:
    def __init__(self):
        self.classification_agent = ClassificationAgent()
        self.response_agent = ResponseAgent()
        self.storage_agent = StorageAgent()

    async def run(self, email_body: str) -> str:
        """
        Orchestrates the classification and response generation for an email.
        
        Args:
            email_body (str): The body of the email to process.
        Returns:
            str: The generated response for the email.
        """
        category = self.classification_agent.classify(email_body)
        response = self.response_agent.generate_response(email_body, category)
        self.storage_agent.store(email_body, category, response)

        return response