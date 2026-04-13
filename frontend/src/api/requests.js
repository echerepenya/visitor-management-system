import api from './index';

export default {
  getActive() {
    return api.get('/api/requests');
  },

  complete(id) {
    return api.post(`/api/requests/${id}/complete`);
  }
};
