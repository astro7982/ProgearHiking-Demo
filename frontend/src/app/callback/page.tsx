"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mountain, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { handleCallback, getOktaAuth } from "@/lib/okta";

type CallbackStatus = "processing" | "success" | "error";

export default function CallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState<CallbackStatus>("processing");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        const oktaAuth = getOktaAuth();

        // Check if this is a redirect from Okta
        if (oktaAuth.isLoginRedirect()) {
          await oktaAuth.handleLoginRedirect();
          setStatus("success");

          // Redirect to chat after a brief delay
          setTimeout(() => {
            router.push("/chat");
          }, 1500);
        } else {
          // Not a valid callback, redirect to home
          router.push("/");
        }
      } catch (err) {
        console.error("Callback error:", err);
        setStatus("error");
        setError(err instanceof Error ? err.message : "Authentication failed");
      }
    };

    processCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-stone-50 to-forest-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center p-8"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-forest-500 to-forest-700 flex items-center justify-center shadow-xl">
            <Mountain className="h-8 w-8 text-white" />
          </div>
        </div>

        {/* Status */}
        {status === "processing" && (
          <div className="space-y-4">
            <Loader2 className="h-12 w-12 text-forest-600 animate-spin mx-auto" />
            <div>
              <h2 className="text-xl font-semibold text-stone-800 mb-2">
                Completing Sign In...
              </h2>
              <p className="text-stone-500">
                Please wait while we verify your credentials.
              </p>
            </div>
          </div>
        )}

        {status === "success" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="h-16 w-16 rounded-full bg-forest-100 flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-10 w-10 text-forest-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-stone-800 mb-2">
                Welcome Back!
              </h2>
              <p className="text-stone-500">
                Redirecting you to the chat...
              </p>
            </div>
          </motion.div>
        )}

        {status === "error" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center mx-auto">
              <AlertCircle className="h-10 w-10 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-stone-800 mb-2">
                Authentication Failed
              </h2>
              <p className="text-stone-500 mb-4">{error}</p>
              <button
                onClick={() => router.push("/")}
                className="text-forest-600 hover:text-forest-700 font-medium"
              >
                Return to Home
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
