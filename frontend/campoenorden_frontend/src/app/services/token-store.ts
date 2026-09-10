export const tokenStore: { token: string | null } = {
  token: typeof localStorage !== 'undefined' ? localStorage.getItem('jwt_token') : null,
};

export function setToken(token: string | null): void {
  tokenStore.token = token;
  if (typeof localStorage !== 'undefined') {
    if (token) {
      localStorage.setItem('jwt_token', token);
    } else {
      localStorage.removeItem('jwt_token');
    }
  }
}