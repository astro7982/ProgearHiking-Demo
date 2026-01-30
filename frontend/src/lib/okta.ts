import { OktaAuth, AccessToken, IDToken } from "@okta/okta-auth-js";

const oktaConfig = {
  issuer: process.env.NEXT_PUBLIC_OKTA_ISSUER || "https://your-org.okta.com",
  clientId: process.env.NEXT_PUBLIC_OKTA_CLIENT_ID || "",
  redirectUri:
    typeof window !== "undefined"
      ? `${window.location.origin}/callback`
      : "http://localhost:3000/callback",
  scopes: ["openid", "profile", "email", "offline_access"],
  pkce: true,
  tokenManager: {
    storage: "localStorage",
  },
};

let oktaAuthInstance: OktaAuth | null = null;

export function getOktaAuth(): OktaAuth {
  if (typeof window === "undefined") {
    throw new Error("OktaAuth can only be used in browser");
  }

  if (!oktaAuthInstance) {
    oktaAuthInstance = new OktaAuth(oktaConfig);
  }

  return oktaAuthInstance;
}

export interface UserInfo {
  sub: string;
  email: string;
  name: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
  groups?: string[];
}

export async function getUserInfo(): Promise<UserInfo | null> {
  try {
    const oktaAuth = getOktaAuth();
    const user = await oktaAuth.getUser();
    return user as UserInfo;
  } catch {
    return null;
  }
}

export async function getAccessToken(): Promise<string | null> {
  try {
    const oktaAuth = getOktaAuth();
    const tokenManager = oktaAuth.tokenManager;
    const token = await tokenManager.get("accessToken") as AccessToken | undefined;
    return token?.accessToken || null;
  } catch {
    return null;
  }
}

export async function getIdToken(): Promise<string | null> {
  try {
    const oktaAuth = getOktaAuth();
    const tokenManager = oktaAuth.tokenManager;
    const token = await tokenManager.get("idToken") as IDToken | undefined;
    return token?.idToken || null;
  } catch {
    return null;
  }
}

export async function signIn(): Promise<void> {
  const oktaAuth = getOktaAuth();
  await oktaAuth.signInWithRedirect();
}

export async function signOut(): Promise<void> {
  const oktaAuth = getOktaAuth();
  await oktaAuth.signOut();
}

export async function handleCallback(): Promise<void> {
  const oktaAuth = getOktaAuth();
  await oktaAuth.handleLoginRedirect();
}

export async function isAuthenticated(): Promise<boolean> {
  try {
    const oktaAuth = getOktaAuth();
    return await oktaAuth.isAuthenticated();
  } catch {
    return false;
  }
}
