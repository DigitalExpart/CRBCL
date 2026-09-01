import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import {
  Printer,
  ShieldAlert,
  ArrowLeft,
  Heart,
  Calendar,
  User,
  Phone,
  Home,
  AlertTriangle,
  FileCheck,
} from 'lucide-react';

export default function ChildPassport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPassport();
  }, [id]);

  const loadPassport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await reportingApi.getChildPassport(id);
      setPassport(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load Child Passport');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Generating Child Passport...</div>;
  }

  if (error) {
    return (
      <div className="p-6 max-w-lg mx-auto text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-destructive mx-auto" />
        <h2 className="text-xl font-bold text-foreground">Access Restricted</h2>
        <p className="text-sm text-muted-foreground">{error}</p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { demographics, contacts, medical, cultural_information, placement_history } = passport;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 print:p-0 print:max-w-none">
      {/* Top Bar (Hidden during print) */}
      <div className="flex items-center justify-between print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
        >
          <Printer className="w-4 h-4" /> Print / Save PDF
        </button>
      </div>

      {/* Passport Document Container */}
      <div className="bg-card border border-border rounded-xl p-8 space-y-6 shadow-sm print:border-none print:shadow-none print:p-0">
        {/* Official Header */}
        <div className="border-b-2 border-primary/20 pb-4 flex items-start justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest text-primary">
              Chief Red Bear Children's Lodge
            </div>
            <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Child Passport</h1>
            <p className="text-xs text-muted-foreground mt-1">
              Official Child Continuity Record & Transfer Profile
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground space-y-0.5">
            <div>Generated: {new Date(passport.generated_at).toLocaleString()}</div>
            <div className="font-semibold text-foreground">ID: {demographics.child_id.slice(0, 8)}</div>
          </div>
        </div>

        {/* Demographics Summary Box */}
        <div className="p-4 bg-muted/40 rounded-xl border border-border grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-xs text-muted-foreground font-medium">Full Name</div>
            <div className="font-bold text-foreground text-base">{demographics.full_name}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground font-medium">Date of Birth</div>
            <div className="font-semibold text-foreground">
              {demographics.date_of_birth ? demographics.date_of_birth : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground font-medium">Gender</div>
            <div className="font-semibold text-foreground">{demographics.gender || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground font-medium">Indigenous Identity</div>
            <div className="font-semibold text-foreground">{demographics.indigenous_status || 'N/A'}</div>
          </div>
        </div>

        {/* Emergency Contacts */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase text-foreground tracking-wider flex items-center gap-2 border-b border-border pb-1">
            <Phone className="w-4 h-4 text-primary" /> Emergency Contacts
          </h2>
          {contacts && contacts.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              {contacts.map((c, i) => (
                <div key={i} className="p-3 bg-card border border-border rounded-lg flex items-center justify-between">
                  <div>
                    <div className="font-medium text-foreground">{c.value}</div>
                    <div className="text-xs text-muted-foreground uppercase">{c.contact_type}</div>
                  </div>
                  {c.is_primary && (
                    <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded text-[10px] font-bold">
                      Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground italic">No emergency contacts logged.</div>
          )}
        </div>

        {/* Medical Section (Permission-Aware Redaction) */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase text-foreground tracking-wider flex items-center gap-2 border-b border-border pb-1">
            <Heart className="w-4 h-4 text-rose-500" /> Medical & Health Profile
          </h2>

          {medical.redacted ? (
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-3 text-amber-700 dark:text-amber-400">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <div className="text-xs font-medium">
                <strong>Section Redacted:</strong> Medical profile details omitted (Requires client.medical.read capability).
              </div>
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-4 bg-muted/20 p-3 rounded-lg">
                <div>
                  <span className="text-xs text-muted-foreground">Health Card Number:</span>{' '}
                  <span className="font-medium">{medical.health_number || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Blood Type:</span>{' '}
                  <span className="font-medium">{medical.blood_type || 'N/A'}</span>
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1">Known Allergies</div>
                {medical.allergies && medical.allergies.length > 0 ? (
                  <ul className="list-disc list-inside text-xs space-y-1 text-foreground">
                    {medical.allergies.map((a, idx) => (
                      <li key={idx}>
                        <span className="font-medium">{a.allergen}</span> ({a.severity})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-xs text-muted-foreground italic">No known allergies logged.</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Placement History */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase text-foreground tracking-wider flex items-center gap-2 border-b border-border pb-1">
            <Home className="w-4 h-4 text-primary" /> Placement History
          </h2>
          {placement_history && placement_history.length > 0 ? (
            <div className="space-y-2 text-sm">
              {placement_history.map((p, idx) => (
                <div key={idx} className="p-3 border border-border rounded-lg flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-foreground">{p.provider_name || 'Placement Home'}</div>
                    <div className="text-xs text-muted-foreground">
                      {p.placement_type} • Start: {p.start_date || 'N/A'}
                    </div>
                  </div>
                  <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs font-medium">
                    {p.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground italic">No out-of-home placement history.</div>
          )}
        </div>

        {/* Mandatory Confidentiality Footer Banner */}
        <div className="border-t border-border pt-4 text-center">
          <p className="text-[11px] font-semibold text-muted-foreground">
            {passport.confidentiality_notice}
          </p>
        </div>
      </div>
    </div>
  );
}
