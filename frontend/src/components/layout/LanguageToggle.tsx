import type { Language } from "../../i18n";

interface LanguageToggleProps {
  language: Language;
  onChange: (language: Language) => void;
}

export function LanguageToggle({ language, onChange }: LanguageToggleProps) {
  return (
    <div className="language-toggle" aria-label="Language switcher">
      <button
        className={language === "zh" ? "active" : ""}
        onClick={() => onChange("zh")}
        type="button"
      >
        中文
      </button>
      <button
        className={language === "en" ? "active" : ""}
        onClick={() => onChange("en")}
        type="button"
      >
        EN
      </button>
    </div>
  );
}
