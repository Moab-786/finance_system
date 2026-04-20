import { createContext, useState } from "react";
import { api, decodeRoleFromToken } from "../api/client";
import {
    clearAuthSession,
    getAccessToken,
    getStoredRole,
    setAuthSession,
} from "../api/tokenStorage";

const AuthContext = createContext(null);

function toFormBody(payload) {
    const form = new URLSearchParams();
    Object.entries(payload).forEach(([key, value]) => {
        form.append(key, value);
    });
    return form;
}

export function AuthProvider({ children }) {
    const [accessToken, setAccessToken] = useState(getAccessToken());
    const [role, setRole] = useState(getStoredRole());
    const [isAuthLoading, setIsAuthLoading] = useState(false);

    const isAuthenticated = Boolean(accessToken);

    async function login({ username, password }) {
        setIsAuthLoading(true);
        try {
            const response = await api.post(
                "/auth/login",
                toFormBody({ username, password }),
                {
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                },
            );

            const nextAccessToken = response.data.access_token;
            const nextRefreshToken = response.data.refresh_token;
            const nextRole = decodeRoleFromToken(nextAccessToken);

            setAuthSession({
                accessToken: nextAccessToken,
                refreshToken: nextRefreshToken,
                role: nextRole,
            });
            setAccessToken(nextAccessToken);
            setRole(nextRole);
            return response.data;
        } finally {
            setIsAuthLoading(false);
        }
    }

    async function signup({ username, email, password, role: selectedRole }) {
        await api.post("/auth/register", {
            username,
            email,
            password,
            role: selectedRole,
        });

        return login({ username, password });
    }

    async function logout() {
        const tokenToRevoke = getAccessToken();
        try {
            if (tokenToRevoke) {
                await api.post("/auth/logout", { token: tokenToRevoke });
            }
        } catch {
            // Logout must still clear local state even if revoke call fails.
        } finally {
            clearAuthSession();
            setAccessToken(null);
            setRole(null);
        }
    }

    const value = {
        accessToken,
        role,
        isAuthenticated,
        isAuthLoading,
        login,
        signup,
        logout,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
