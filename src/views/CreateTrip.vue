<template>
  <div class="create-trip">
    <div class="wizard-steps">
      <div :class="['step', { active: currentStep === 1 }]">1. Type de trajet</div>
      <div :class="['step', { active: currentStep === 2 }]">2. Départ</div>
      <div :class="['step', { active: currentStep === 3 }]">3. Destination</div>
      <div :class="['step', { active: currentStep === 4 }]">4. Confirmation</div>
    </div>

    <!-- Étape 1: Type de trajet -->
    <div v-if="currentStep === 1" class="step-content">
      <h2>Type de trajet</h2>
      <div class="trip-types">
        <button 
          v-for="type in tripTypes" 
          :key="type.id"
          @click="selectTripType(type)"
          :class="['trip-type-btn', { selected: selectedTripType?.id === type.id }]"
        >
          {{ type.icon }} {{ type.name }}
        </button>
      </div>
    </div>

    <!-- Étape 2: Départ -->
    <div v-if="currentStep === 2" class="step-content">
      <h2>Point de départ</h2>
      <LocationSearch 
        @location-selected="handleDepartureSelected"
        :error="departureError"
      />
      <div v-if="departure" class="selected-info">
        Départ sélectionné: {{ departure.name }} ({{ departure.zipcode }})
      </div>
    </div>

    <!-- Étape 3: Destination -->
    <div v-if="currentStep === 3" class="step-content">
      <h2>Destination</h2>
      <LocationSearch 
        @location-selected="handleDestinationSelected"
        :error="destinationError"
      />
      <div v-if="destination" class="selected-info">
        Destination sélectionnée: {{ destination.name }} ({{ destination.zipcode }})
      </div>
    </div>

    <!-- Étape 4: Confirmation -->
    <div v-if="currentStep === 4" class="step-content">
      <h2>Confirmation du trajet</h2>
      <div class="trip-summary">
        <div class="summary-item">
          <strong>Type:</strong> {{ selectedTripType?.name }}
        </div>
        <div class="summary-item">
          <strong>Départ:</strong> {{ departure?.name }} ({{ departure?.zipcode }})
        </div>
        <div class="summary-item">
          <strong>Destination:</strong> {{ destination?.name }} ({{ destination?.zipcode }})
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav">
      <button 
        v-if="currentStep > 1" 
        @click="previousStep"
        class="nav-btn back"
      >
        Retour
      </button>
      <button 
        v-if="currentStep < 4" 
        @click="nextStep"
        :disabled="!canProceed"
        class="nav-btn next"
      >
        Suivant
      </button>
      <button 
        v-else 
        @click="createTrip"
        class="nav-btn confirm"
      >
        Créer le trajet
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import LocationSearch from '@/components/LocationSearch.vue';
import type { Location } from '@/services/LocationService';

interface TripType {
  id: number;
  name: string;
  icon: string;
}

export default defineComponent({
  components: { LocationSearch },
  setup() {
    const currentStep = ref(1);
    const selectedTripType = ref<TripType | null>(null);
    const departure = ref<Location | null>(null);
    const destination = ref<Location | null>(null);
    const departureError = ref('');
    const destinationError = ref('');

    const tripTypes: TripType[] = [
      { id: 1, name: 'Trajet unique', icon: '🚗' },
      { id: 2, name: 'Trajet régulier', icon: '🔄' }
    ];

    const canProceed = computed(() => {
      switch (currentStep.value) {
        case 1: return selectedTripType.value !== null;
        case 2: return departure.value !== null;
        case 3: return destination.value !== null;
        default: return true;
      }
    });

    const selectTripType = (type: TripType) => {
      selectedTripType.value = type;
    };

    const handleDepartureSelected = (location: Location) => {
      departure.value = location;
      departureError.value = '';
    };

    const handleDestinationSelected = (location: Location) => {
      if (location.zipcode === departure.value?.zipcode) {
        destinationError.value = 'La destination ne peut pas être identique au départ';
        return;
      }
      destination.value = location;
      destinationError.value = '';
    };

    const nextStep = () => {
      if (canProceed.value) {
        currentStep.value++;
      }
    };

    const previousStep = () => {
      currentStep.value--;
    };

    const createTrip = async () => {
      // Implémentation de la création finale du trajet
      console.log('Création du trajet:', {
        type: selectedTripType.value,
        departure: departure.value,
        destination: destination.value
      });
    };

    return {
      currentStep,
      selectedTripType,
      departure,
      destination,
      tripTypes,
      departureError,
      destinationError,
      canProceed,
      selectTripType,
      handleDepartureSelected,
      handleDestinationSelected,
      nextStep,
      previousStep,
      createTrip
    };
  }
});
</script>

<style scoped>
.create-trip {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.wizard-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 20px 0;
  border-bottom: 2px solid #eee;
}

.step {
  flex: 1;
  text-align: center;
  color: #666;
  position: relative;
}

.step.active {
  color: #4CAF50;
  font-weight: bold;
}

.step-content {
  margin: 20px 0;
}

.trip-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.trip-type-btn {
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 1.1em;
  transition: all 0.3s;
}

.trip-type-btn.selected {
  border-color: #4CAF50;
  background: #e8f5e9;
}

.selected-info {
  margin-top: 10px;
  padding: 10px;
  background: #e8f5e9;
  border-radius: 4px;
}

.wizard-nav {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #eee;
}

.nav-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.nav-btn.back {
  background: #f5f5f5;
  color: #666;
}

.nav-btn.next {
  background: #4CAF50;
  color: white;
}

.nav-btn.next:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.nav-btn.confirm {
  background: #2196F3;
  color: white;
}

.trip-summary {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.summary-item {
  margin: 10px 0;
}
</style>
