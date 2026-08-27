import React from "react";

function StatCard({
  title,
  value,
  icon,
  subtitle,
  gradient = "from-blue-500 to-indigo-600",
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${gradient} p-6 text-white shadow-lg transition-all duration-300 hover:-translate-y-1 hover:shadow-xl`}
    >
      {/* Decorative circle */}
      <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10" />

      <div className="relative z-10">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white/80">
              {title}
            </p>
          </div>

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 text-xl backdrop-blur-sm">
            {icon}
          </div>
        </div>

        <h2 className="text-3xl font-bold tracking-tight">
          {value}
        </h2>

        {subtitle && (
          <p className="mt-2 text-xs text-white/70">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}

export default StatCard;