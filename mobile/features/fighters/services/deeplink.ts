/** Fighter deeplinks + sharing */
export const fighterDeeplinks = {
  profile: (id: string) => `mma://fighter/${id}`,
  stats: (id: string) => `mma://fighter/${id}/stats`,
  compare: (a: string, b: string) => `mma://compare/${a}/${b}`,
};

export const fighterSharing = {
  profile: (name: string, id: string) => ({
    title: `${name} — MMA Intelligence`,
    message: `Check out ${name} on MMA Intelligence`,
    url: `https://mma.app/fighter/${id}`,
  }),
  comparison: (a: string, b: string) => ({
    title: `${a} vs ${b} — MMA Intelligence`,
    message: `${a} vs ${b}: Tale of the Tape`,
    url: `https://mma.app/compare/${a}/${b}`,
  }),
};
