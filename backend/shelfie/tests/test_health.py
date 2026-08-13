import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_health_check_endpoint():
    """Test GET /api/health/ returns 200 OK and {'status': 'ok'}."""
    client = APIClient()
    url = reverse('health_check')
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
