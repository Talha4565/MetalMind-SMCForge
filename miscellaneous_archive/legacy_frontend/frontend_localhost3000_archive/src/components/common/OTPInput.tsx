import { useRef, useEffect, KeyboardEvent, ClipboardEvent } from 'react';
import { Box, TextField } from '@mui/material';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';

type OTPInputProps<T extends FieldValues> = {
  name: Path<T>;
  control: Control<T>;
  length?: number;
  disabled?: boolean;
  onComplete?: (otp: string) => void;
};

/**
 * OTPInput Component
 * 6-digit OTP input with auto-focus and auto-submit
 */
export function OTPInput<T extends FieldValues>({
  name,
  control,
  length = 6,
  disabled = false,
  onComplete,
}: OTPInputProps<T>) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Focus first input on mount
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string, onChange: (val: string) => void, currentValue: string) => {
    // Only allow numbers
    if (value && !/^\d+$/.test(value)) {
      return;
    }

    // Get new OTP value
    const otpArray = currentValue.split('');
    otpArray[index] = value;
    const newOtp = otpArray.join('');

    onChange(newOtp);

    // Auto-focus next input
    if (value && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    // Call onComplete when all digits are filled
    if (newOtp.length === length && onComplete) {
      onComplete(newOtp);
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLDivElement>, currentValue: string, onChange: (val: string) => void) => {
    if (e.key === 'Backspace' && !currentValue[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLDivElement>, onChange: (val: string) => void) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    
    // Only process if it's all digits and matches length
    if (/^\d+$/.test(pastedData) && pastedData.length === length) {
      onChange(pastedData);
      inputRefs.current[length - 1]?.focus();
      
      if (onComplete) {
        onComplete(pastedData);
      }
    }
  };

  return (
    <Controller
      name={name}
      control={control}
      render={({ field: { value = '', onChange }, fieldState: { error } }) => (
        <Box>
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
            {Array.from({ length }).map((_, index) => (
              <TextField
                key={index}
                inputRef={(el) => (inputRefs.current[index] = el)}
                value={value[index] || ''}
                onChange={(e) => handleChange(index, e.target.value, onChange, value)}
                onKeyDown={(e) => handleKeyDown(index, e as KeyboardEvent<HTMLDivElement>, value, onChange)}
                onPaste={(e) => handlePaste(e as ClipboardEvent<HTMLDivElement>, onChange)}
                disabled={disabled}
                error={!!error}
                inputProps={{
                  maxLength: 1,
                  style: {
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 600,
                  },
                }}
                sx={{
                  width: 56,
                  '& input': {
                    padding: '12px',
                  },
                }}
              />
            ))}
          </Box>
          {error && (
            <Box sx={{ color: 'error.main', fontSize: '0.75rem', mt: 1, textAlign: 'center' }}>
              {error.message}
            </Box>
          )}
        </Box>
      )}
    />
  );
}
