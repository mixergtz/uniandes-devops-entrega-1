import os
import uuid
import random
import string

from locust import HttpUser, task, between

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "dev-token-123")


def random_email(domain="example.com"):
    prefix = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{prefix}@{domain}"


class BlacklistUser(HttpUser):
    """
    Usuario de prueba que:
    - Llama /health
    - Hace POST /blacklists con correos válidos
    - Hace GET /blacklists/<email> válidos y no válidos
    - También genera algunos errores intencionales para New Relic:
      * Auth inválido
      * Body inválido
      * Endpoint inexistente
    """
    wait_time = between(0.1, 0.5)

    blacklisted_emails = []

    def on_start(self):
        # Precargar algunos correos válidos
        for _ in range(3):
            email = random_email()
            self._add_to_blacklist(email)

    def _headers(self):
        return {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json",
        }

    def _add_to_blacklist(self, email):
        payload = {
            "email": email,
            "app_uuid": str(uuid.uuid4()),
            "blocked_reason": "load-test",
        }
        with self.client.post(
            "/blacklists",
            json=payload,
            headers=self._headers(),
            name="POST /blacklists",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201):
                self.blacklisted_emails.append(email)
            else:
                response.failure(
                    f"Status code {response.status_code}: {response.text}"
                )

    # =========
    # TAREAS "NORMALES"
    # =========

    @task(2)
    def health_check(self):
        self.client.get("/health", name="GET /health")

    @task(4)
    def add_email_blacklist(self):
        email = random_email()
        self._add_to_blacklist(email)

    @task(4)
    def check_blacklist(self):
        if self.blacklisted_emails and random.random() < 0.7:
            email = random.choice(self.blacklisted_emails)
        else:
            email = random_email()

        with self.client.get(
            f"/blacklists/{email}",
            headers=self._headers(),
            name="GET /blacklists/{email}",
            catch_response=True,
        ) as response:
            # Aceptamos 200 y 404 como respuestas “esperadas”
            if response.status_code not in (200, 404):
                response.failure(
                    f"Unexpected status code {response.status_code}: {response.text}"
                )

    # =========
    # TAREAS PARA GENERAR ERRORES
    # =========

    @task(1)
    def invalid_auth_error(self):
        """
        Fuerza errores 401/403 usando un token incorrecto.
        Útil para que New Relic registre errores de autenticación.
        """
        headers = {
            "Authorization": "Bearer INVALID_TOKEN",
            "Content-Type": "application/json",
        }
        email = random_email()
        with self.client.get(
            f"/blacklists/{email}",
            headers=headers,
            name="GET /blacklists invalid auth",
            catch_response=True,
        ) as response:
            # Aquí esperamos explícitamente un error, así que marcamos failure
            # para que Locust lo registre como tal.
            if response.status_code < 400:
                response.failure(
                    f"Expected auth error, got {response.status_code}: {response.text}"
                )

    @task(1)
    def invalid_body_error(self):
        """
        Fuerza errores 400/422 enviando un JSON mal formado
        o faltando campos requeridos.
        """
        bad_payload = {
            # Falta 'email', 'app_uuid', etc.
            "foo": "bar",
        }
        with self.client.post(
            "/blacklists",
            json=bad_payload,
            headers=self._headers(),
            name="POST /blacklists invalid body",
            catch_response=True,
        ) as response:
            if response.status_code < 400:
                response.failure(
                    f"Expected validation error, got {response.status_code}: {response.text}"
                )

    @task(1)
    def not_found_error(self):
        """
        Fuerza errores 404 llamando a un endpoint que no existe.
        Ideal para ver cómo se ve en New Relic un “Not Found”.
        """
        with self.client.get(
            "/blacklists/non-existing-endpoint",
            headers=self._headers(),
            name="GET /blacklists invalid path",
            catch_response=True,
        ) as response:
            # Aquí lo "esperado" es 404, así que cualquier otra cosa la marcamos como failure rara
            if response.status_code != 404:
                response.failure(
                    f"Expected 404, got {response.status_code}: {response.text}"
                )
