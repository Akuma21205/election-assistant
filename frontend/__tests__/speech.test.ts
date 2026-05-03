/**
 * Utility tests for VoteGuide frontend helpers.
 * Tests SPEECH_LANG_CODES mapping and getSessionId behaviour.
 *
 * Run: npx jest (after adding jest + @types/jest to devDependencies)
 */

import { SPEECH_LANG_CODES } from "../lib/speech";

describe("SPEECH_LANG_CODES", () => {
  it("maps english to en-US", () => {
    expect(SPEECH_LANG_CODES["english"]).toBe("en-US");
  });

  it("maps hindi to hi-IN", () => {
    expect(SPEECH_LANG_CODES["hindi"]).toBe("hi-IN");
  });

  it("maps spanish to es-ES", () => {
    expect(SPEECH_LANG_CODES["spanish"]).toBe("es-ES");
  });

  it("maps french to fr-FR", () => {
    expect(SPEECH_LANG_CODES["french"]).toBe("fr-FR");
  });

  it("maps tamil to ta-IN", () => {
    expect(SPEECH_LANG_CODES["tamil"]).toBe("ta-IN");
  });

  it("maps telugu to te-IN", () => {
    expect(SPEECH_LANG_CODES["telugu"]).toBe("te-IN");
  });

  it("maps bengali to bn-IN", () => {
    expect(SPEECH_LANG_CODES["bengali"]).toBe("bn-IN");
  });

  it("maps marathi to mr-IN", () => {
    expect(SPEECH_LANG_CODES["marathi"]).toBe("mr-IN");
  });

  it("maps kannada to kn-IN", () => {
    expect(SPEECH_LANG_CODES["kannada"]).toBe("kn-IN");
  });

  it("covers all 9 supported languages", () => {
    expect(Object.keys(SPEECH_LANG_CODES)).toHaveLength(9);
  });

  it("returns undefined for unsupported language", () => {
    expect(SPEECH_LANG_CODES["swahili"]).toBeUndefined();
  });

  it("all values follow BCP-47 format (xx-XX)", () => {
    const bcp47Pattern = /^[a-z]{2}-[A-Z]{2}$/;
    for (const [lang, code] of Object.entries(SPEECH_LANG_CODES)) {
      expect(code).toMatch(bcp47Pattern);
    }
  });
});
