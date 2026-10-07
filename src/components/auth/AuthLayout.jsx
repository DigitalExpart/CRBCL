import React, { useEffect } from "react";
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
  useEffect(() => {
    // Auth pages invariant: Always retain original clean white lodge branding
    const root = document.documentElement;
    root.classList.remove('dark');
    root.classList.add('theme-crbcl');
  }, []);

  return (
    <div className="auth-layout min-h-screen flex items-center justify-center bg-[#FAF8F6] px-4 py-8 text-[#1F1A17]">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          {showLogo ? (
            <div className="flex justify-center mb-4">
              <Link
                to="/"
                className="inline-block focus:outline-none focus:ring-2 focus:ring-[#8B2626]/40 rounded-xl transition-transform hover:scale-105 duration-200"
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
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#8B2626] mb-4">
                <Icon className="w-7 h-7 text-white" aria-hidden="true" />
              </div>
            )
          )}
          {title && <h1 className="text-3xl font-bold tracking-tight text-[#1F1A17] font-heading">{title}</h1>}
          {subtitle && <p className="text-[#786F6B] mt-2 text-sm max-w-sm mx-auto">{subtitle}</p>}
        </div>
        {children && (
          <div className="bg-white rounded-2xl shadow-sm border border-[#E8E3DF] p-8 text-[#1F1A17]">
            {children}
          </div>
        )}
        {footer && (
          <div className="text-center text-sm text-[#786F6B] mt-6">{footer}</div>
        )}
      </div>
    </div>
  );
}
