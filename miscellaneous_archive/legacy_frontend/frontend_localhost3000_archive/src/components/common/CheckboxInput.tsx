import { FormControlLabel, Checkbox, FormHelperText, Box } from '@mui/material';
import { Controller, Control, FieldValues, Path } from 'react-hook-form';

type CheckboxInputProps<T extends FieldValues> = {
  name: Path<T>;
  control: Control<T>;
  label: string | React.ReactNode;
  disabled?: boolean;
};

/**
 * CheckboxInput Component
 * Checkbox with react-hook-form integration
 */
export function CheckboxInput<T extends FieldValues>({
  name,
  control,
  label,
  disabled = false,
}: CheckboxInputProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <Box>
          <FormControlLabel
            control={
              <Checkbox
                {...field}
                checked={field.value || false}
                disabled={disabled}
                color={error ? 'error' : 'primary'}
              />
            }
            label={label}
          />
          {error && (
            <FormHelperText error sx={{ mt: 0, ml: 2 }}>
              {error.message}
            </FormHelperText>
          )}
        </Box>
      )}
    />
  );
}
