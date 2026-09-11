// Matches tailored bullets back to base bullets by source_bullet_id
// (no longer by text, since tailoring may now rewrite wording).
export function computeExperienceDiff(baseExperiences, tailoredExperiences) {
  return baseExperiences.map((baseExp) => {
    const tailoredExp = tailoredExperiences.find(
      (t) => t.company === baseExp.company && t.title === baseExp.title,
    );
    const tailoredBySourceId = new Map(
      (tailoredExp?.bullets ?? []).map((b) => [b.source_bullet_id, b]),
    );

    const bulletDiffs = baseExp.bullets.map((bullet) => {
      const tailoredMatch = tailoredBySourceId.get(bullet.id);
      return {
        text: bullet.text,
        kept: Boolean(tailoredMatch),
        rewritten: tailoredMatch ? tailoredMatch.text !== bullet.text : false,
      };
    });

    return { company: baseExp.company, title: baseExp.title, bulletDiffs };
  });
}