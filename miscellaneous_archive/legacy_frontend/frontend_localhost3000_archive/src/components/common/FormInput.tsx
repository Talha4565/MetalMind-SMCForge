import { TextField, TextFieldProps } from '@mui/material';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';

type FormInputProps<T extends FieldValues> = {
  name: Path<T>;
  control: Control<T>;
  label: string;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  autoComplete?: string;
  multiline?: boolean;
  rows?: number;
} & Omit<TextFieldProps, 'name' | 'label' | 'type'>;

/**
 * FormInput Component
 * Reusable text input with react-hook-form integration
 */
export function FormInput<T extends FieldValues>({
  name,
  control,
  label,
  type = 'text',
  placeholder,
  disabled = false,
  autoComplete,
  multiline = false,
  rows,
  ...rest
}: FormInputProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          {...rest}
          label={label}
          type={type}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          multiline={multiline}
          rows={rows}
          error={!!error}
          helperText={error?.message}
          fullWidth
          variant="outlined"
        />
      )}
    />
  );
}
