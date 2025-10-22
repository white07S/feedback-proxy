import React, { useState } from "react";

export default function FeedbackForm({ projects, onSubmit }) {
  const [form, setForm] = useState({
    project_key: "",
    type: "bug",
    title: "",
    description: "",
    severity: "medium"
  });

  const disabled = !form.project_key || !form.title || !form.description;

  const handleSubmit = () => {
    if (!disabled) {
      onSubmit(form);
      // Reset form after submission
      setForm({
        project_key: "",
        type: "bug",
        title: "",
        description: "",
        severity: "medium"
      });
    }
  };

  return (
    <div className="border border-gray-300 bg-white p-4 mb-4">
      <h3 className="text-xl font-bold text-black mb-4">New Feedback</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-black mb-1">
            Project
          </label>
          <select
            value={form.project_key}
            onChange={e => setForm({ ...form, project_key: e.target.value })}
            className="w-full p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
          >
            <option value="">Select...</option>
            {projects.map(p => <option key={p.key} value={p.key}>{p.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-black mb-1">
            Type
          </label>
          <select
            value={form.type}
            onChange={e => setForm({ ...form, type: e.target.value })}
            className="w-full p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
          >
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
          </select>
        </div>
      </div>

      <div className="mt-3">
        <label className="block text-sm font-medium text-black mb-1">
          Title
        </label>
        <input
          value={form.title}
          onChange={e => setForm({ ...form, title: e.target.value })}
          className="w-full p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
          placeholder="Enter title..."
        />
      </div>

      <div className="mt-3">
        <label className="block text-sm font-medium text-black mb-1">
          Description
        </label>
        <textarea
          rows={4}
          value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          className="w-full p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
          placeholder="Enter description..."
        />
      </div>

      <div className="mt-3">
        <label className="block text-sm font-medium text-black mb-1">
          Severity
        </label>
        <select
          value={form.severity}
          onChange={e => setForm({ ...form, severity: e.target.value })}
          className="w-full p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <button
        disabled={disabled}
        onClick={handleSubmit}
        className={`mt-4 px-6 py-2 font-medium text-white ${
          disabled
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-ubs-red hover:bg-red-700 cursor-pointer'
        } transition-colors`}
      >
        Submit
      </button>
    </div>
  );
}