import { useState } from "react";
import { Settings as SettingsIcon, User, Shield, Bell } from "lucide-react";

function Settings() {
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="mx-auto max-w-5xl">
      {/* HEADER */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 shadow-sm">
            <SettingsIcon size={22} color="white" />
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              Settings
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Manage your AI Rice Factory system settings.
            </p>
          </div>
        </div>
      </div>

      {/* ACCOUNT */}
      <div className="mb-5 rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
          <User size={19} className="text-indigo-600" />

          <div>
            <h2 className="font-semibold text-gray-900">
              Account
            </h2>

            <p className="text-xs text-gray-500">
              Current logged-in account
            </p>
          </div>
        </div>

        <div className="grid gap-5 p-6 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              Username
            </label>

            <input
              type="text"
              value="staff"
              readOnly
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 outline-none"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              Role
            </label>

            <input
              type="text"
              value="Staff"
              readOnly
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 outline-none"
            />
          </div>
        </div>
      </div>

      {/* AI SYSTEM */}
      <div className="mb-5 rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
          <Shield size={19} className="text-indigo-600" />

          <div>
            <h2 className="font-semibold text-gray-900">
              AI System
            </h2>

            <p className="text-xs text-gray-500">
              AI Factory Assistant configuration
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm font-semibold text-gray-900">
              AI Assistant
            </p>

            <p className="mt-1 text-xs text-gray-500">
              Factory intelligence and financial analysis are enabled.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

            <span className="text-sm font-medium text-green-600">
              Online
            </span>
          </div>
        </div>
      </div>

      {/* NOTIFICATIONS */}
      <div className="rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4">
          <Bell size={19} className="text-indigo-600" />

          <div>
            <h2 className="font-semibold text-gray-900">
              Notifications
            </h2>

            <p className="text-xs text-gray-500">
              Manage factory system notifications
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm font-semibold text-gray-900">
              System Notifications
            </p>

            <p className="mt-1 text-xs text-gray-500">
              Receive alerts about important factory activity.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setNotifications(!notifications)}
            className={`relative h-6 w-11 rounded-full transition ${
              notifications ? "bg-indigo-600" : "bg-gray-300"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow transition ${
                notifications ? "left-6" : "left-1"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;