import React, { useEffect, useState } from "react";
import { listProjects, listFeedback, createFeedback, patchFeedback, addComment, listPeople } from "../components/feedback/api";
import FeedbackForm from "../components/feedback/FeedbackForm";
import FeedbackFilters from "../components/feedback/FeedbackFilters";
import FeedbackList from "../components/feedback/FeedbackList";

const currentUser = "preetam"; // hard-coded for now

export default function Feedback() {
  const [projects, setProjects] = useState([]);
  const [people, setPeople] = useState([]);
  const [filters, setFilters] = useState({ project_key: "", status: "", type: "", search: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("submit");
  const pageSize = 20;

  useEffect(() => {
    const loadMeta = async () => {
      try {
        const [proj, folks] = await Promise.all([listProjects(), listPeople()]);
        setProjects(proj);
        setPeople(folks);
      } catch (err) {
        console.error("Failed to load initial data:", err);
        setError("Failed to load projects or people. Please ensure the backend is running.");
      }
    };
    loadMeta();
  }, []);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page, page_size: pageSize };
      if (filters.project_key) params.project_key = filters.project_key;
      if (filters.status) params.status = filters.status;
      if (filters.type) params.type = filters.type;
      if (filters.search) params.search = filters.search;

      const result = await listFeedback(params);
      setData(result);
    } catch (err) {
      console.error("Failed to load feedback:", err);
      setError("Failed to load feedback. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, page]);

  const submitFeedback = async (payload) => {
    try {
      await createFeedback({ ...payload, created_by: currentUser });
      setPage(1);
      load();
    } catch (err) {
      console.error("Failed to create feedback:", err);
      setError("Failed to create feedback. Please try again.");
    }
  };

  const updateFeedback = async (id, patch) => {
    try {
      await patchFeedback(id, { ...patch, updated_by: currentUser });
      load();
    } catch (err) {
      console.error("Failed to update feedback:", err);
      setError("Failed to update feedback. Please try again.");
    }
  };

  const submitComment = async (id, body) => {
    try {
      await addComment(id, { body, created_by: currentUser });
      load();
    } catch (err) {
      console.error("Failed to add comment:", err);
      setError("Failed to add comment. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-black mb-2">Project Feedback</h1>
          <div className="h-1 w-32 bg-ubs-red"></div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700">
            {error}
          </div>
        )}

        <div className="mb-6 flex border-b border-gray-200">
          {[
            { id: "submit", label: "Log Feedback" },
            { id: "view", label: "View Feedback" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === tab.id
                  ? "text-ubs-red border-b-2 border-ubs-red"
                  : "text-gray-600 hover:text-ubs-red"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "submit" && (
          <div className="mb-6">
            <FeedbackForm projects={projects} people={people} onSubmit={submitFeedback} />
          </div>
        )}

        {activeTab === "view" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-black mb-3">Filter Feedback</h2>
              <FeedbackFilters projects={projects} value={filters} onChange={setFilters} />
            </div>

            <div>
              <h2 className="text-xl font-bold text-black mb-3">Feedback Items</h2>
              {loading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin h-8 w-8 border-4 border-ubs-red border-t-transparent"></div>
                  <p className="mt-2 text-gray-600">Loading...</p>
                </div>
              ) : (
                <FeedbackList
                  data={data}
                  onPageChange={setPage}
                  pageSize={pageSize}
                  onUpdate={updateFeedback}
                  onComment={submitComment}
                  people={people}
                  currentUser={currentUser}
                />
              )}
            </div>
          </>
        )}

        <div className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-600">
          Logged in as: <span className="font-medium text-black">{currentUser}</span>
        </div>
      </div>
    </div>
  );
}
