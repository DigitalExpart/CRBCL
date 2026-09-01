import React, { useState } from 'react';
import { 
  Megaphone, 
  Share2, 
  Plus, 
  CheckCircle2, 
  Clock, 
  Send, 
  ShieldCheck, 
  Lock,
  Globe
} from 'lucide-react';

export default function CommunicationsHub() {
  const [posts, setPosts] = useState([
    {
      id: 'post-101',
      title: 'Annual Community Wellness Gathering 2026',
      content: 'Join Chief Red Bear Children\'s Lodge for our annual Community Wellness Day! Free activities, cultural workshops, and lunch provided.',
      target_platforms: 'META',
      status: 'PUBLISHED',
      published_at: '2026-08-28T14:00:00Z',
      created_by: 'Staff Member'
    },
    {
      id: 'post-102',
      title: 'Fall Youth Cultural Mentorship Registration Open',
      content: 'Registration is now open for our Fall Mentorship Program. Open to youth ages 12-18.',
      target_platforms: 'META',
      status: 'APPROVED',
      published_at: null,
      created_by: 'Communications Co-ordinator'
    }
  ]);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [platform, setPlatform] = useState('META');
  const [showModal, setShowModal] = useState(false);

  const handleCreatePost = (e) => {
    e.preventDefault();
    if (!title || !content) return;
    const newPost = {
      id: `post-${Date.now()}`,
      title,
      content,
      target_platforms: platform,
      status: 'DRAFT',
      published_at: null,
      created_by: 'Current User'
    };
    setPosts([newPost, ...posts]);
    setTitle('');
    setContent('');
    setShowModal(false);
  };

  const handleApprove = (postId) => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, status: 'APPROVED' } : p));
  };

  const handlePublish = (postId) => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, status: 'PUBLISHED', published_at: new Date().toISOString() } : p));
  };

  const statusBadge = (status) => {
    if (status === 'PUBLISHED') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1"><Globe className="w-3 h-3" /> Published</span>;
    }
    if (status === 'APPROVED') {
      return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-950 text-blue-300 border border-blue-800 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Approved</span>;
    }
    return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1"><Clock className="w-3 h-3" /> Draft</span>;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-pink-600 to-rose-600 shadow-lg shadow-pink-900/30">
              <Megaphone className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Public Communications & Outreach Hub
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Social media content foundation & two-stage approval workflow.
              </p>
            </div>
          </div>

          <button 
            onClick={() => setShowModal(true)}
            className="px-4 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white shadow-lg shadow-pink-900/30 transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Draft New Announcement
          </button>
        </div>
      </div>

      {/* Security Isolation Notice */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-pink-900/50 backdrop-blur-md flex items-start gap-3 text-xs md:text-sm text-slate-300">
          <Lock className="w-5 h-5 text-pink-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-pink-300">Domain Isolation Guarantee:</strong> Public Communications posts operate completely independently from CRBCL Case Management. Posts contain zero foreign keys to Case or Client records.
          </div>
        </div>
      </div>

      {/* Posts List */}
      <div className="max-w-7xl mx-auto space-y-4">
        {posts.map((post) => (
          <div key={post.id} className="rounded-2xl bg-slate-900/90 border border-slate-800 p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-semibold text-slate-100">{post.title}</h3>
                {statusBadge(post.status)}
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-xs font-mono border border-slate-700">{post.target_platforms}</span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">{post.content}</p>
              <div className="text-xs text-slate-500 flex items-center gap-4">
                <span>Created by: {post.created_by}</span>
                {post.published_at && <span>Published: {new Date(post.published_at).toLocaleDateString()}</span>}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {post.status === 'DRAFT' && (
                <button 
                  onClick={() => handleApprove(post.id)}
                  className="px-4 py-2 rounded-xl bg-blue-950 hover:bg-blue-900 text-blue-200 border border-blue-800 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4 text-blue-400" /> Approve Post
                </button>
              )}
              {post.status === 'APPROVED' && (
                <button 
                  onClick={() => handlePublish(post.id)}
                  className="px-4 py-2 rounded-xl bg-emerald-950 hover:bg-emerald-900 text-emerald-200 border border-emerald-800 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Send className="w-4 h-4 text-emerald-400" /> Publish Now
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <h2 className="text-xl font-bold text-slate-100">Draft Public Announcement</h2>
            <form onSubmit={handleCreatePost} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Post Title</label>
                <input 
                  type="text" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-pink-500" 
                  placeholder="Title of community announcement..."
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Content</label>
                <textarea 
                  value={content} 
                  onChange={(e) => setContent(e.target.value)}
                  rows={4}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-pink-500" 
                  placeholder="Public announcement body text..."
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Target Platforms</label>
                <select 
                  value={platform} 
                  onChange={(e) => setPlatform(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-pink-500"
                >
                  <option value="META">Meta (Facebook & Instagram)</option>
                  <option value="X">X (Twitter)</option>
                  <option value="LINKEDIN">LinkedIn</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-sm font-semibold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-5 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white text-sm font-semibold"
                >
                  Save Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
