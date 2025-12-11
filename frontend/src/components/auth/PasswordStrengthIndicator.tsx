'use client';

interface PasswordStrengthIndicatorProps {
  password: string;
}

type StrengthLevel = 'weak' | 'medium' | 'strong';

interface StrengthCriteria {
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasNumber: boolean;
  hasSpecialChar: boolean;
}

/**
 * PasswordStrengthIndicator Component
 * Displays a visual strength bar and criteria checklist for password validation
 *
 * @param {string} password - The password to evaluate
 * @returns Visual indicator with color-coded strength bar and criteria checklist
 */
export function PasswordStrengthIndicator({ password }: PasswordStrengthIndicatorProps) {
  // Evaluate password criteria
  const criteria: StrengthCriteria = {
    hasMinLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
  };

  // Calculate strength level
  const metCriteriaCount = Object.values(criteria).filter(Boolean).length;
  let strength: StrengthLevel;
  let strengthColor: string;
  let strengthText: string;
  let strengthWidth: string;

  if (metCriteriaCount <= 1) {
    strength = 'weak';
    strengthColor = 'bg-red-500';
    strengthText = 'Weak';
    strengthWidth = 'w-1/3';
  } else if (metCriteriaCount <= 3) {
    strength = 'medium';
    strengthColor = 'bg-yellow-500';
    strengthText = 'Medium';
    strengthWidth = 'w-2/3';
  } else {
    strength = 'strong';
    strengthColor = 'bg-green-500';
    strengthText = 'Strong';
    strengthWidth = 'w-full';
  }

  // Don't show indicator if password is empty
  if (password.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 mt-2">
      {/* Strength Bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">Password Strength</span>
          <span className={`text-sm font-semibold ${
            strength === 'weak' ? 'text-red-500' :
            strength === 'medium' ? 'text-yellow-600' :
            'text-green-600'
          }`}>
            {strengthText}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full ${strengthColor} transition-all duration-300 ease-in-out ${strengthWidth}`}
          />
        </div>
      </div>

      {/* Criteria Checklist */}
      <div className="space-y-1 text-sm">
        <CriteriaItem met={criteria.hasMinLength} text="At least 8 characters" />
        <CriteriaItem met={criteria.hasUppercase} text="One uppercase letter" />
        <CriteriaItem met={criteria.hasNumber} text="One number" />
        <CriteriaItem met={criteria.hasSpecialChar} text="One special character" />
      </div>
    </div>
  );
}

function CriteriaItem({ met, text }: { met: boolean; text: string }) {
  return (
    <div className="flex items-center gap-2">
      {met ? (
        <svg
          className="w-4 h-4 text-green-600"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M5 13l4 4L19 7"></path>
        </svg>
      ) : (
        <svg
          className="w-4 h-4 text-gray-400"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      )}
      <span className={met ? 'text-green-700' : 'text-gray-500'}>{text}</span>
    </div>
  );
}
