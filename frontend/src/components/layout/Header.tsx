"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Mountain,
  LogOut,
  User,
  Settings,
  Shield,
  ChevronDown,
  Cloud,
  Package,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { UserInfo } from "@/lib/okta";
import type { UserAccess } from "@/lib/api";

interface HeaderProps {
  user: UserInfo | null;
  access: UserAccess | null;
  onSignOut: () => void;
}

export function Header({ user, access, onSignOut }: HeaderProps) {
  const pathname = usePathname();

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-lg supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex items-center justify-center h-10 w-10 rounded-xl bg-gradient-to-br from-forest-500 to-forest-700 shadow-lg group-hover:shadow-xl transition-shadow duration-200">
            <Mountain className="h-6 w-6 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg text-stone-800 tracking-tight">
              ProGear
            </span>
            <span className="text-[10px] text-stone-500 -mt-1 font-medium uppercase tracking-wider">
              Hiking Co.
            </span>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-1">
          <Link
            href="/chat"
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200",
              pathname === "/chat"
                ? "bg-forest-100 text-forest-700"
                : "text-stone-600 hover:bg-stone-100"
            )}
          >
            Chat
          </Link>
          <Link
            href="/dashboard"
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200",
              pathname === "/dashboard"
                ? "bg-forest-100 text-forest-700"
                : "text-stone-600 hover:bg-stone-100"
            )}
          >
            Dashboard
          </Link>
        </nav>

        {/* Right Side */}
        <div className="flex items-center gap-3">
          {/* Agent Status Indicators */}
          {access && (
            <div className="hidden md:flex items-center gap-2">
              <div
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                  access.salesforce.connected
                    ? "bg-blue-100 text-blue-700"
                    : "bg-stone-100 text-stone-400"
                )}
              >
                <Cloud className="h-3 w-3" />
                <span>Salesforce</span>
                {access.salesforce.connected && (
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                )}
              </div>
              <div
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                  access.inventory.authorized
                    ? "bg-forest-100 text-forest-700"
                    : "bg-stone-100 text-stone-400"
                )}
              >
                <Package className="h-3 w-3" />
                <span>Inventory</span>
                {access.inventory.authorized && (
                  <div className="h-1.5 w-1.5 rounded-full bg-forest-500 animate-pulse" />
                )}
              </div>
            </div>
          )}

          {/* User Menu */}
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 px-2 hover:bg-stone-100"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-forest-600 text-white text-sm">
                      {getInitials(user.name || user.email)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden md:flex flex-col items-start">
                    <span className="text-sm font-medium text-stone-800">
                      {user.name || user.email}
                    </span>
                    {user.groups && user.groups.length > 0 && (
                      <span className="text-[10px] text-stone-500">
                        {user.groups[0]}
                      </span>
                    )}
                  </div>
                  <ChevronDown className="h-4 w-4 text-stone-400" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="font-medium">{user.name}</span>
                    <span className="text-xs text-stone-500 font-normal">
                      {user.email}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />

                {/* Access Info */}
                {access && (
                  <>
                    <DropdownMenuLabel className="text-xs text-stone-500 font-normal">
                      Agent Access
                    </DropdownMenuLabel>
                    <div className="px-2 py-1.5 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <Cloud className="h-3 w-3 text-blue-500" />
                          <span>Salesforce</span>
                        </div>
                        <Badge
                          variant={
                            access.salesforce.connected ? "success" : "secondary"
                          }
                          className="text-[10px] px-1.5"
                        >
                          {access.salesforce.connected
                            ? "Connected"
                            : "Not Connected"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <Package className="h-3 w-3 text-forest-500" />
                          <span>Inventory</span>
                        </div>
                        <Badge
                          variant={
                            access.inventory.authorized ? "success" : "secondary"
                          }
                          className="text-[10px] px-1.5"
                        >
                          {access.inventory.authorized
                            ? "Authorized"
                            : "No Access"}
                        </Badge>
                      </div>
                    </div>
                    <DropdownMenuSeparator />
                  </>
                )}

                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Shield className="mr-2 h-4 w-4" />
                  <span>Security</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Activity className="mr-2 h-4 w-4" />
                  <span>Activity Log</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onSignOut}
                  className="text-red-600 focus:text-red-600"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="default">Sign In</Button>
          )}
        </div>
      </div>
    </header>
  );
}
