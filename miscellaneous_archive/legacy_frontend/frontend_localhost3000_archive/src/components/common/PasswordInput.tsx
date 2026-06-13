import { useState } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  TextFieldProps,
  Box,
  LinearProgress,
  Typography,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';
import { calculatePasswordStrength } from '@/features/auth/utils/validation';

type PasswordInputProps<T extends FieldValues> = {
  name: Path<T>;
  control: Control<T>;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  autoComplete?: string;
  showStrength?: boolean;
} & Omit<TextFieldProps, 'name' | 'label' | 'type'>;

/**
 * PasswordInput Component
 * Password field with visibility toggle and optional strength indicator
 */
export function PasswordInput<T extends FieldValues>({
  name,
  control,
  label,
  placeholder,
  disabled = false,
  autoComplete = 'current-password',
  showStrength = false,
  ...rest
}: PasswordInputProps<T>) {
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const strength = showStrength && field.value
          ? calculatePasswordStrength(field.value)
          : null;

        return (
          <Box>
            <TextField
              {...field}
              {...rest}
              label={label}
              type={showPassword ? 'text' : 'password'}
              placeholder={placeholder}
              disabled={disabled}
              autoComplete={autoComplete}
              error={!!error}
              helperText={error?.message}
              fullWidth
              variant="outlined"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={togglePasswordVisibility}
                      edge="end"
                      disabled={disabled}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            {showStrength && strength && field.value && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <LinearProgress
                    variant="determinate"
                    value={(strength.score / 6) * 100}
                    color={strength.color}
                    sx={{ flex: 1, height: 6, borderRadius: 3 }}
                  />
                  <Typography
                    variant="caption"
                    color={`${strength.color}.main`}
                    fontWeight={500}
                  >
                    {strength.label}
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        );
      }}
    />
  );
}
