import React from "react";

export default function FeedbackFilters({ projects, value, onChange }) {
  const set = (k, v) => onChange({ ...value, [k]: v });

  return (
    <div className="flex flex-wrap gap-2 items-center mb-4 p-3 bg-gray-50 border border-gray-200">
      <select
        value={value.project_key}
        onChange={e => set("project_key", e.target.value)}
        className="p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
      >
        <option value="">All Projects</option>
        {projects.map(p => <option key={p.key} value={p.key}>{p.name}</option>)}
      </select>

      <select
        value={value.type}
        onChange={e => set("type", e.target.value)}
        className="p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
      >
        <option value="">All Types</option>
        <option value="bug">Bug</option>
        <option value="feature">Feature</option>
      </select>

      <select
        value={value.status}
        onChange={e => set("status", e.target.value)}
        className="p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
      >
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="in_progress">In Progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>

      <input
        placeholder="Search title/description..."
        value={value.search}
        onChange={e => set("search", e.target.value)}
        className="flex-1 min-w-[200px] p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
      />

      <button
        onClick={() => onChange({ project_key: "", status: "", type: "", search: "" })}
        className="px-4 py-2 text-ubs-red border border-ubs-red bg-white hover:bg-red-50 transition-colors"
      >
        Clear
      </button>
    </div>
  );
}
