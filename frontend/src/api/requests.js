import api from './index';

export default {
  getActive() {
    return api.get('/requests');
  },

  complete(id) {
    return api.post(`/requests/${id}/complete`);
  }
};
