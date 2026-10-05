import React from "react";
import { Link } from "react-router-dom";
import crbclLogo from "@/assets/crbcl-logo.png";

export default function AuthLayout({ 
  icon: Icon, 
  title = "", 
  subtitle = "", 
  footer = null, 
  children = null,
  showLogo = true,
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          {showLogo ? (
            <div className="flex justify-center mb-4">
              <Link
                to="/"
                className="inline-block focus:outline-none focus:ring-2 focus:ring-primary/40 rounded-xl transition-transform hover:scale-105 duration-200"
                title="Chief Red Bear Children's Lodge"
              >
                <img
                  src={crbclLogo}
                  alt="Chief Red Bear Children's Lodge"
                  className="h-28 w-auto object-contain mx-auto"
                />
              </Link>
            </div>
          ) : (
            Icon && (
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary mb-4">
                <Icon className="w-7 h-7 text-primary-foreground" aria-hidden="true" />
              </div>
            )
          )}
          {title && <h1 className="text-3xl font-bold tracking-tight text-foreground font-heading">{title}</h1>}
          {subtitle && <p className="text-muted-foreground mt-2 text-sm max-w-sm mx-auto">{subtitle}</p>}
        </div>
        {children && (
          <div className="bg-card rounded-2xl shadow-sm border border-border p-8">
            {children}
          </div>
        )}
        {footer && (
          <div className="text-center text-sm text-muted-foreground mt-6">{footer}</div>
        )}
      </div>
    </div>
  );
}
