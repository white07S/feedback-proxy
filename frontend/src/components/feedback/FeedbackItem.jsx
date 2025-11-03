import React, { useState, useEffect, useMemo } from "react";
import { listComments } from "./api";

export default function FeedbackItem({ item, expanded, onToggle, onUpdate, onComment, people, currentUser }) {
  const [patch, setPatch] = useState({ status: "", assignee: "", resolution: "" });
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState([]);
  const isMine = item.assignee === currentUser;
  const peopleLookup = useMemo(
    () => Object.fromEntries(people.map(person => [person.username, person.name])),
    [people]
  );

  useEffect(() => {
    if (expanded) {
      listComments(item.id).then(setComments);
    }
  }, [expanded, item.id]);

  useEffect(() => {
    if (!expanded) {
      setPatch({ status: "", assignee: "", resolution: "" });
    }
  }, [expanded, item.id]);

  const cleanPatch = useMemo(
    () => Object.fromEntries(Object.entries(patch).filter(([, v]) => v !== "")),
    [patch]
  );
  const hasRestrictedChanges = Boolean(cleanPatch.status || cleanPatch.resolution);
  const updateDisabled = Object.keys(cleanPatch).length === 0 || (!isMine && hasRestrictedChanges);

  const handleUpdate = () => {
    if (updateDisabled) return;
    onUpdate(item.id, cleanPatch);
    setPatch({ status: "", assignee: "", resolution: "" });
  };

  const handleComment = () => {
    if (comment.trim()) {
      onComment(item.id, comment.trim());
      setComment("");
      // Reload comments
      setTimeout(() => {
        listComments(item.id).then(setComments);
      }, 100);
    }
  };

  const severityColors = {
    low: "text-green-600",
    medium: "text-yellow-600",
    high: "text-orange-600",
    critical: "text-red-600"
  };

  const statusColors = {
    open: "bg-blue-100 text-blue-800",
    pending: "bg-gray-100 text-gray-800",
    in_progress: "bg-yellow-100 text-yellow-800",
    resolved: "bg-green-100 text-green-800",
    closed: "bg-gray-100 text-gray-800"
  };

  const typeColors = {
    bug: "bg-red-100 text-red-800",
    feature: "bg-purple-100 text-purple-800"
  };

  return (
    <div className="border border-gray-200 bg-white mb-3 shadow-sm">
      <div
        className="flex justify-between items-start p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-bold text-black">#{item.id}</span>
            <span className="text-sm text-gray-600">[{item.project_key}]</span>
            <span className={`px-2 py-1 text-xs ${typeColors[item.type]}`}>
              {item.type.toUpperCase()}
            </span>
            <span className={`px-2 py-1 text-xs ${statusColors[item.status]}`}>
              {item.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <h4 className="font-semibold text-black text-lg">{item.title}</h4>
          <div className="text-sm text-gray-600 mt-1">
            <span className={severityColors[item.severity] || "text-gray-600"}>
              Severity: {item.severity || "N/A"}
            </span>
            <span className="mx-2">•</span>
            <span>By: {item.created_by}</span>
            <span className="mx-2">•</span>
            <span>Created: {new Date(item.created_at).toLocaleString()}</span>
          </div>
        </div>
        <div className="text-gray-400">
          {expanded ? '▲' : '▼'}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-200 p-4">
          <div className="mb-4">
            <h5 className="font-medium text-black mb-2">Description</h5>
            <p className="text-gray-700 whitespace-pre-wrap">{item.description}</p>
          </div>

          {item.assignee && (
            <div className="mb-4">
              <span className="font-medium text-black">Assignee: </span>
              <span className="text-gray-700">{peopleLookup[item.assignee] || item.assignee}</span>
            </div>
          )}

          {item.resolution && (
            <div className="mb-4">
              <span className="font-medium text-black">Resolution: </span>
              <span className="text-gray-700">{item.resolution}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4 p-3 bg-gray-50">
            <select
              value={patch.status}
              onChange={e => setPatch({ ...patch, status: e.target.value })}
              disabled={!isMine}
              className={`p-2 border border-gray-300 ${isMine ? "bg-white" : "bg-gray-100"} text-black focus:border-ubs-red focus:outline-none`}
            >
              <option value="">Set status...</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>

            <select
              value={patch.assignee}
              onChange={e => setPatch({ ...patch, assignee: e.target.value })}
              className="p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
            >
              <option value="">Assign to...</option>
              {people.map(person => (
                <option key={person.username} value={person.username}>
                  {person.name}
                </option>
              ))}
            </select>

            <input
              placeholder="Resolution"
              value={patch.resolution}
              onChange={e => setPatch({ ...patch, resolution: e.target.value })}
              disabled={!isMine}
              className={`p-2 border border-gray-300 ${isMine ? "bg-white" : "bg-gray-100"} text-black focus:border-ubs-red focus:outline-none`}
            />

            <button
              onClick={handleUpdate}
              disabled={updateDisabled}
              className={`p-2 ${
                updateDisabled
                  ? "bg-gray-400 text-white cursor-not-allowed"
                  : "bg-ubs-red text-white hover:bg-red-700 cursor-pointer"
              } transition-colors`}
            >
              Update
            </button>
          </div>

          {!isMine && (
            <div className="mb-4 text-sm text-gray-600">
              Only the assigned user can update status or resolution.
            </div>
          )}

          {comments.length > 0 && (
            <div className="mb-4">
              <h5 className="font-medium text-black mb-2">Comments ({comments.length})</h5>
              <div className="space-y-2">
                {comments.map((c) => (
                  <div key={c.id} className="p-2 bg-gray-50 border-l-4 border-gray-300">
                    <div className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">{c.created_by}</span>
                      <span className="mx-2">•</span>
                      <span>{new Date(c.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-gray-700">{c.body}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <input
              className="flex-1 p-2 border border-gray-300 bg-white text-black focus:border-ubs-red focus:outline-none"
              placeholder="Add a comment..."
              value={comment}
              onChange={e => setComment(e.target.value)}
            />
            <button
              onClick={handleComment}
              className="px-4 py-2 bg-ubs-red text-white hover:bg-red-700 transition-colors"
            >
              Comment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
