from locust import HttpUser, task, between

class PersonaLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def generate_responses(self):
        self.client.post("/", json={
            "prompt": "What do you think?",
            "personas": [{"name": "LoadTester"}]
        })
