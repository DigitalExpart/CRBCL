import { api } from './client';

export const authApi = {
  login: (email, password) => api.auth.loginViaEmailPassword(email, password),
  logout: (redirectUrl) => api.auth.logout(redirectUrl),
  me: () => api.auth.me(),
  register: (data) => api.auth.register(data),
  forgotPassword: (email) => api.auth.resetPasswordRequest(email),
  resetPassword: (data) => api.auth.resetPassword(data),
};
