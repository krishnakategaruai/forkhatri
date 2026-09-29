"use client";

/**
 * The samaj as an organisation: national office bearers, state and city chapters with
 * their office bearers, and the teams looking after each module. Modelled on multi-level
 * community bodies (Rotary / Lions districts and clubs): people first, then structure.
 */
import { useState } from "react";
import { admin, type Chapter } from "@/lib/admin-api";
import { Dialog, Empty, errorMessage, ErrorLine, Field, Loading, PageHead, Section, useConsole, useLoad } from "./kit";
import { AppointDialog, AssignmentRow } from "./Team";

export default function Organisation() {
  const { t, can, me, changed, version } = useConsole();
  const org = useLoad(() => admin.org(), [version]);
  const data = org.data;
  const error = org.error ? errorMessage(t, org.error) : null;
  const [adding, setAdding] = useState<{ kind: "state" | "city"; parent: Chapter | null } | null>(null);
  const [appointIn, setAppointIn] = useState<Chapter | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const mayManage = (c: Chapter) => can("roles.manage") || me.managed_chapters.includes(c.key);
  const states = data?.chapters.filter((c) => c.kind === "state") ?? [];

  return (
    <div className="adm-page">
      <PageHead
        title={t("orgTitle")}
        sub={t("orgSub")}
        actions={
          can("org.manage") && (
            <button type="button" className="adm-btn" onClick={() => setAdding({ kind: "state", parent: null })}>
              {t("addState")}
            </button>
          )
        }
      />
      {notice && (
        <p className="adm-success" role="status">
          {notice}
        </p>
      )}
      <ErrorLine error={error} />
      {!data ? (
        <Loading />
      ) : (
        <>
          <Section title={t("nationalOffice")}>
            {data.national.length === 0 ? (
              <Empty>{t("nobodyYet")}</Empty>
            ) : (
              <ul className="adm-list adm-card">
                {data.national.map((a) => (
                  <AssignmentRow key={a.id} a={a} />
                ))}
              </ul>
            )}
          </Section>

          <Section title={t("chapters")}>
            {states.length === 0 ? (
              <Empty>{t("noChapters")}</Empty>
            ) : (
              <div className="adm-chapters">
                {states.map((state) => {
                  const cities = data.chapters.filter((c) => c.parent_key === state.key);
                  return (
                    <article key={state.key} className="adm-card adm-chapter">
                      <header className="adm-chapter-head">
                        <div>
                          <h3>{state.name}</h3>
                          <p className="adm-muted">{t("citiesN", { n: cities.length })}</p>
                        </div>
                        <div className="adm-actions">
                          {mayManage(state) && (
                            <button type="button" className="adm-btn small" onClick={() => setAppointIn(state)}>
                              {t("appoint")}
                            </button>
                          )}
                          {(can("org.manage") || me.managed_chapters.includes(state.key)) && (
                            <button type="button" className="adm-btn small" onClick={() => setAdding({ kind: "city", parent: state })}>
                              {t("addCity")}
                            </button>
                          )}
                        </div>
                      </header>
                      <Bearers chapter={state} />
                      {cities.map((city) => (
                        <div key={city.key} className="adm-city">
                          <div className="adm-chapter-head">
                            <h4>{city.name}</h4>
                            {mayManage(city) && (
                              <button type="button" className="adm-btn small" onClick={() => setAppointIn(city)}>
                                {t("appoint")}
                              </button>
                            )}
                          </div>
                          <Bearers chapter={city} />
                        </div>
                      ))}
                    </article>
                  );
                })}
              </div>
            )}
          </Section>

          {(data.staff ?? []).length > 0 && (
            <Section title={t("platformTeam")}>
              <ul className="adm-list adm-card">
                {(data.staff ?? []).map((a) => (
                  <AssignmentRow key={a.id} a={a} />
                ))}
              </ul>
            </Section>
          )}

          <Section title={t("moduleTeams")}>
            {data.modules.length === 0 ? (
              <Empty>{t("nobodyYet")}</Empty>
            ) : (
              <ul className="adm-list adm-card">
                {data.modules.map((a) => (
                  <AssignmentRow key={a.id} a={a} />
                ))}
              </ul>
            )}
          </Section>
        </>
      )}

      <AddChapter
        adding={adding}
        onClose={() => setAdding(null)}
        onDone={() => {
          setAdding(null);
          changed();
        }}
      />
      <AppointDialog
        open={!!appointIn}
        preset={appointIn ? { scope_kind: "chapter", scope_key: appointIn.key, scope_name: appointIn.name } : undefined}
        onClose={() => setAppointIn(null)}
        onDone={(message) => {
          setAppointIn(null);
          setNotice(message);
          changed();
        }}
      />
    </div>
  );
}

function Bearers({ chapter }: { chapter: Chapter }) {
  const { t } = useConsole();
  if (chapter.office_bearers.length === 0) return <p className="adm-muted adm-bearers-empty">{t("noBearers")}</p>;
  return (
    <ul className="adm-list">
      {chapter.office_bearers.map((a) => (
        <AssignmentRow key={a.id} a={a} />
      ))}
    </ul>
  );
}

function AddChapter({ adding, onClose, onDone }: { adding: { kind: "state" | "city"; parent: Chapter | null } | null; onClose: () => void; onDone: () => void }) {
  const { t } = useConsole();
  const title = adding?.kind === "city" ? `${t("addCity")} · ${adding.parent?.name ?? ""}` : t("addState");
  return (
    <Dialog open={!!adding} onClose={onClose} title={title}>
      {adding && <AddChapterForm adding={adding} onClose={onClose} onDone={onDone} />}
    </Dialog>
  );
}

/** Mounted each time the dialog opens, so the form always starts empty. */
function AddChapterForm({ adding, onClose, onDone }: { adding: { kind: "state" | "city"; parent: Chapter | null }; onClose: () => void; onDone: () => void }) {
  const { t } = useConsole();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <Field label={t("chapterName")}>
        <input className="adm-input" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} placeholder={adding?.kind === "city" ? t("cityPlaceholder") : t("statePlaceholder")} />
      </Field>
      <ErrorLine error={error} />
      <div className="adm-actions end">
        <button type="button" className="adm-btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button
          type="button"
          className="adm-btn primary"
          disabled={name.trim().length < 2}
          onClick={async () => {
            try {
              if (adding) await admin.addChapter({ name: name.trim(), kind: adding.kind, parent_key: adding.parent?.key ?? null });
              onDone();
            } catch (e) {
              setError(errorMessage(t, e));
            }
          }}
        >
          {t("add")}
        </button>
      </div>
    </>
  );
}
