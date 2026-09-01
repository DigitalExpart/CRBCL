import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportingApi } from '../api/reporting';
import { Printer, ArrowLeft, User, Phone, FileText } from 'lucide-react';

export default function ParentPassport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPassport();
  }, [id]);

  const loadPassport = async () => {
    setLoading(true);
    try {
      const res = await reportingApi.getParentPassport(id);
      setPassport(res.data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Generating Parent Passport...</div>;
  }

  if (!passport) {
    return <div className="p-8 text-center text-destructive">Failed to load Parent Passport.</div>;
  }

  const { demographics, contacts } = passport;

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6 print:p-0 print:max-w-none">
      <div className="flex items-center justify-between print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-3 py-1.5 border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button
          onClick={() => window.print()}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
        >
          <Printer className="w-4 h-4" /> Print / Save PDF
        </button>
      </div>

      <div className="bg-card border border-border rounded-xl p-8 space-y-6 shadow-sm print:border-none print:shadow-none print:p-0">
        <div className="border-b-2 border-primary/20 pb-4 flex items-start justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest text-primary">
              Chief Red Bear Children's Lodge
            </div>
            <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Parent Passport</h1>
            <p className="text-xs text-muted-foreground mt-1">Authorized Parent Identity & Family Continuity Summary</p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <div>Generated: {new Date(passport.generated_at).toLocaleDateString()}</div>
          </div>
        </div>

        <div className="p-4 bg-muted/40 rounded-xl border border-border grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-xs text-muted-foreground font-medium">Full Name</div>
            <div className="font-bold text-foreground text-base">{demographics.full_name}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground font-medium">Date of Birth</div>
            <div className="font-semibold text-foreground">{demographics.date_of_birth || 'N/A'}</div>
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-sm font-bold uppercase text-foreground tracking-wider border-b border-border pb-1">
            Registered Contacts
          </h2>
          {contacts && contacts.length > 0 ? (
            <div className="space-y-2 text-sm">
              {contacts.map((c, i) => (
                <div key={i} className="p-3 border border-border rounded-lg flex items-center justify-between">
                  <span className="font-medium">{c.value}</span>
                  <span className="text-xs text-muted-foreground uppercase">{c.contact_type}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground italic">No contact details logged.</div>
          )}
        </div>

        <div className="border-t border-border pt-4 text-center">
          <p className="text-[11px] font-semibold text-muted-foreground">{passport.confidentiality_notice}</p>
        </div>
      </div>
    </div>
  );
}
