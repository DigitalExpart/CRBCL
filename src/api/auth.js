import { api } from './client';

export const authApi = {
  login: (email, password) => api.auth.loginViaEmailPassword(email, password),
  loginViaPin: (email, pin) => api.auth.loginViaPin(email, pin),
  logout: (redirectUrl) => api.auth.logout(redirectUrl),
  me: () => api.auth.me(),
  register: (data) => api.auth.register(data),
  forgotPassword: (email) => api.auth.resetPasswordRequest(email),
  resetPassword: (data) => api.auth.resetPassword(data),
  setPin: (pin) => api.auth.setPin(pin),
  getPinStatus: (email) => api.auth.getPinStatus(email),
};
