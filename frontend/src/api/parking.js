import api from './index';

export default {
  getActiveRequests() {
    return api.get('/api/parking/requests');
  },

  getStatus() {
    return api.get('/api/parking/status');
  },

  issueKeyfob(id) {
    return api.post(`/api/parking/${id}/issue-keyfob`);
  },

  returnKeyfob(id) {
    return api.post(`/api/parking/${id}/return-keyfob`);
  },

  resetKeyfob() {
    return api.post('/api/parking/reset-keyfob');
  },

  overrideSpots(free_spots) {
    return api.post('/api/parking/override-spots', { free_spots });
  }
};
