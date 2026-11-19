import Aura from '@primevue/themes/aura';
import { definePreset } from '@primevue/themes';

// 统一主色：靛蓝（Indigo），替换原来刺眼的紫色渐变
const MyPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{indigo.50}',
      100: '{indigo.100}',
      200: '{indigo.200}',
      300: '{indigo.300}',
      400: '{indigo.400}',
      500: '{indigo.500}',
      600: '{indigo.600}',
      700: '{indigo.700}',
      800: '{indigo.800}',
      900: '{indigo.900}',
      950: '{indigo.950}'
    },
    colorScheme: {
      light: {
        primary: {
          color: '{indigo.600}',
          hoverColor: '{indigo.700}',
          activeColor: '{indigo.800}'
        },
        formField: {
          hoverBorderColor: '{indigo.400}',
          focusBorderColor: '{indigo.500}'
        }
      }
    }
  },
  components: {
    button: {
      root: {
        borderRadius: '8px',
        paddingX: '1rem',
        paddingY: '0.625rem'
      }
    },
    inputtext: {
      root: { borderRadius: '8px' }
    },
    textarea: {
      root: { borderRadius: '8px' }
    },
    datatable: {
      root: { borderRadius: '12px' }
    },
    dialog: {
      root: { borderRadius: '16px' }
    }
  }
});

export default MyPreset;
