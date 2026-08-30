import { api } from './client';

export const teamsApi = {
  list: () => api.entities.Team.list(),
  get: (id) => api.entities.Team.get(id),
};
