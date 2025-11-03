import React, { useState } from "react";
import FeedbackItem from "./FeedbackItem";

export default function FeedbackList({ data, onPageChange, pageSize, onUpdate, onComment, people, currentUser }) {
  const { items, page, total } = data;
  const [expanded, setExpanded] = useState(null);
  const pages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <div className="flex justify-between items-center mb-4 p-3 bg-gray-50 border border-gray-200">
        <div className="font-medium text-black">
          {total} result{total !== 1 ? 's' : ''}
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className={`px-3 py-1 border ${
              page <= 1
                ? 'border-gray-300 text-gray-400 cursor-not-allowed bg-gray-100'
                : 'border-ubs-red text-ubs-red bg-white hover:bg-red-50 cursor-pointer'
            } transition-colors`}
          >
            Previous
          </button>
          <span className="px-3 text-black">
            Page {page} of {pages}
          </span>
          <button
            disabled={page >= pages}
            onClick={() => onPageChange(page + 1)}
            className={`px-3 py-1 border ${
              page >= pages
                ? 'border-gray-300 text-gray-400 cursor-not-allowed bg-gray-100'
                : 'border-ubs-red text-ubs-red bg-white hover:bg-red-50 cursor-pointer'
            } transition-colors`}
          >
            Next
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 border border-gray-200">
          <p className="text-gray-600 text-lg">No feedback items found</p>
          <p className="text-gray-500 text-sm mt-2">Try adjusting your filters or create a new feedback item</p>
        </div>
      ) : (
        <div>
          {items.map(item => (
            <FeedbackItem
              key={item.id}
              item={item}
              expanded={expanded === item.id}
              onToggle={() => setExpanded(expanded === item.id ? null : item.id)}
              onUpdate={onUpdate}
              onComment={onComment}
              people={people}
              currentUser={currentUser}
            />
          ))}
        </div>
      )}
    </div>
  );
}
