<script lang="ts">
  // A Solar Linear icon (see lib/icons.ts). Inherits the text colour and scales with the font size.
  import { icons, type IconName } from '../lib/icons'

  let { name, size = '1.3em' }: { name: IconName; size?: string } = $props()
</script>

<svg viewBox="0 0 24 24" width={size} height={size} fill="none" aria-hidden="true">{@html icons[name]}</svg>
