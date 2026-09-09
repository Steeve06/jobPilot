from config.test_utils import TwoProfileTestCase
from .models import SearchProfile


class SearchProfileScopingTests(TwoProfileTestCase):
    def setUp(self):
        super().setUp()
        self.own_sp = SearchProfile.objects.create(profile=self.profile_a, name='Mine')
        self.other_sp = SearchProfile.objects.create(profile=self.profile_b, name='Not mine')

    def test_list_only_returns_own_profile_data(self):
        response = self.client.get('/api/search-profiles/')
        names = [row['name'] for row in response.data]
        self.assertIn('Mine', names)
        self.assertNotIn('Not mine', names)

    def test_retrieve_other_profiles_object_returns_404(self):
        response = self.client.get(f'/api/search-profiles/{self.other_sp.id}/')
        self.assertEqual(response.status_code, 404)

    def test_create_assigns_active_profile_not_client_supplied(self):
        response = self.client.post('/api/search-profiles/', {
            'name': 'New Profile', 'title_keywords': [], 'excluded_keywords': [], 'locations': [],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        created = SearchProfile.objects.get(id=response.data['id'])
        self.assertEqual(created.profile_id, self.profile_a.id)