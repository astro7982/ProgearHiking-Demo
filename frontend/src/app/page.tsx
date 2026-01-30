"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Mountain,
  Cloud,
  Package,
  Shield,
  ArrowRight,
  Sparkles,
  Lock,
  Users,
  Activity,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { signIn, isAuthenticated, getOktaAuth } from "@/lib/okta";

const features = [
  {
    icon: Cloud,
    title: "Salesforce Integration",
    description:
      "Access leads, opportunities, accounts, and contacts directly through natural conversation.",
    gradient: "from-blue-500 to-blue-600",
  },
  {
    icon: Package,
    title: "Inventory Management",
    description:
      "Check stock levels, update inventory, and set alerts for low-stock items in real-time.",
    gradient: "from-forest-500 to-forest-600",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description:
      "Okta-powered authentication with granular access control and full audit logging.",
    gradient: "from-stone-600 to-stone-700",
  },
];

const securityFeatures = [
  {
    icon: Lock,
    title: "Workload Identity",
    description: "AI agents have their own identity, separate from users",
  },
  {
    icon: Users,
    title: "Delegated Access",
    description: "Agents act on behalf of users with explicit consent",
  },
  {
    icon: Activity,
    title: "Full Audit Trail",
    description: "Every action tracked and logged for compliance",
  },
  {
    icon: Shield,
    title: "Scoped Permissions",
    description: "Granular control over what agents can access",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const oktaAuth = getOktaAuth();
        const authenticated = await oktaAuth.isAuthenticated();
        setIsLoggedIn(authenticated);
        if (authenticated) {
          router.push("/chat");
        }
      } catch (error) {
        console.error("Auth check failed:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  const handleSignIn = async () => {
    try {
      await signIn();
    } catch (error) {
      console.error("Sign in failed:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-stone-50 to-forest-50">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-forest-500 to-forest-700 flex items-center justify-center animate-pulse">
            <Mountain className="h-7 w-7 text-white" />
          </div>
          <p className="text-stone-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 via-white to-forest-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0 bg-[url('/images/topo-pattern.svg')] bg-repeat" />
        </div>

        <div className="container mx-auto px-4 py-20 md:py-32 relative">
          <div className="max-w-4xl mx-auto text-center">
            {/* Logo */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="flex items-center justify-center gap-3 mb-8"
            >
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-forest-500 to-forest-700 flex items-center justify-center shadow-xl">
                <Mountain className="h-9 w-9 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-3xl font-bold text-stone-800">ProGear</h1>
                <p className="text-sm text-stone-500 font-medium tracking-wider uppercase">
                  Hiking Co.
                </p>
              </div>
            </motion.div>

            {/* Headline */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-6xl font-bold text-stone-800 mb-6 tracking-tight"
            >
              Your AI Assistant for{" "}
              <span className="gradient-text">Sales & Inventory</span>
            </motion.h2>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-xl text-stone-600 mb-10 max-w-2xl mx-auto"
            >
              Manage your Salesforce CRM and inventory through natural
              conversation. Secured by Okta with enterprise-grade access
              control.
            </motion.p>

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Button
                size="xl"
                onClick={handleSignIn}
                className="group shadow-xl hover:shadow-2xl"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Sign in with Okta
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button size="xl" variant="outline">
                Learn More
              </Button>
            </motion.div>

            {/* Trust Badge */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="mt-10 flex items-center justify-center gap-6 text-sm text-stone-500"
            >
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-forest-600" />
                <span>Okta Secured</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-forest-600" />
                <span>SOC 2 Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-forest-600" />
                <span>Full Audit Trail</span>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-stone-800 mb-4">
              Powerful AI Agents at Your Service
            </h3>
            <p className="text-lg text-stone-600 max-w-2xl mx-auto">
              Two specialized agents working together to help you manage your
              business operations efficiently.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="h-full hover:shadow-xl transition-shadow duration-300 border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div
                      className={`h-12 w-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 shadow-lg`}
                    >
                      <feature.icon className="h-6 w-6 text-white" />
                    </div>
                    <h4 className="text-xl font-semibold text-stone-800 mb-2">
                      {feature.title}
                    </h4>
                    <p className="text-stone-600">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section className="py-20 bg-gradient-to-br from-stone-900 to-stone-800 text-white">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-forest-500/20 text-forest-400 text-sm font-medium mb-4">
                <Shield className="h-4 w-4" />
                Powered by Okta
              </div>
              <h3 className="text-3xl font-bold mb-4">
                Enterprise-Grade AI Governance
              </h3>
              <p className="text-lg text-stone-400 max-w-2xl mx-auto">
                Your AI agents have their own identity. Every action is tracked,
                authorized, and auditable.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {securityFeatures.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="text-center p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <div className="h-10 w-10 rounded-lg bg-forest-500/20 flex items-center justify-center mx-auto mb-4">
                    <feature.icon className="h-5 w-5 text-forest-400" />
                  </div>
                  <h4 className="font-semibold mb-2">{feature.title}</h4>
                  <p className="text-sm text-stone-400">{feature.description}</p>
                </motion.div>
              ))}
            </div>

            {/* Token Exchange Flow */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              viewport={{ once: true }}
              className="mt-16 p-8 rounded-2xl bg-white/5 border border-white/10"
            >
              <h4 className="text-xl font-semibold mb-6 text-center">
                How It Works
              </h4>
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                {[
                  { step: "1", text: "You sign in with Okta" },
                  { step: "2", text: "AI agent requests access on your behalf" },
                  { step: "3", text: "Okta verifies permissions" },
                  { step: "4", text: "Scoped token issued to agent" },
                  { step: "5", text: "Agent performs action, fully logged" },
                ].map((item, index) => (
                  <React.Fragment key={item.step}>
                    <div className="flex flex-col items-center text-center">
                      <div className="h-10 w-10 rounded-full bg-forest-500 flex items-center justify-center font-bold mb-2">
                        {item.step}
                      </div>
                      <p className="text-sm text-stone-300 max-w-[120px]">
                        {item.text}
                      </p>
                    </div>
                    {index < 4 && (
                      <ArrowRight className="h-5 w-5 text-stone-600 hidden md:block" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-forest-600 to-forest-700 text-white">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold mb-4">
            Ready to Transform Your Workflow?
          </h3>
          <p className="text-lg text-forest-100 mb-8 max-w-xl mx-auto">
            Start managing your sales and inventory with AI assistance today.
          </p>
          <Button
            size="xl"
            variant="secondary"
            onClick={handleSignIn}
            className="shadow-xl"
          >
            Get Started Now
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-stone-900 text-stone-400">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Mountain className="h-5 w-5 text-forest-500" />
              <span className="font-semibold text-white">ProGear Hiking</span>
            </div>
            <p className="text-sm">
              Demo application showcasing Okta AI Agent Governance
            </p>
            <div className="flex items-center gap-4 text-sm">
              <a href="#" className="hover:text-white transition-colors">
                Privacy
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Terms
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Security
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
