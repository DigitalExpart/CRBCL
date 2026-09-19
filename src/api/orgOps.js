import { api } from './client';

export const orgOpsApi = {
  getHrDashboard: () =>
    api.fetch('/api/v1/org-ops/hr-dashboard').then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw data;
      return data;
    }),
};

export default orgOpsApi;
