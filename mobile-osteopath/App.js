import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useState, useMemo } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, TextInput, Alert, Platform, Image } from 'react-native';
import { Calendar } from 'react-native-calendars';
import NetInfo from '@react-native-community/netinfo';

const getApiBase = () => {
  const envBase = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envBase) return envBase;
  if (Platform.OS === 'web') return 'http://localhost:8000';
  if (Platform.OS === 'android') return 'http://10.0.2.2:8000';
  // For iOS simulator, localhost works; for device use EXPO_PUBLIC_API_BASE_URL
  return 'http://localhost:8000';
};

const API_BASE = getApiBase();
const todayStr = new Date().toISOString().slice(0, 10);

export default function App() {
  const [showIntro, setShowIntro] = useState(true);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [slots, setSlots] = useState([]);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [name, setName] = useState(''); // Add name state
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isOnline, setIsOnline] = useState(true);
  const [tasks, setTasks] = useState([
    { id: 'location', label: 'Select a location', done: false },
    { id: 'date', label: 'Select a date', done: false },
    { id: 'slot', label: 'Select a time slot', done: false },
    { id: 'info', label: 'Enter name, email and phone', done: false }, // Update task label
    { id: 'book', label: 'Book the appointment', done: false },
  ]);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      const online = !!state.isConnected && state.isInternetReachable !== false;
      setIsOnline(online);
    });
    NetInfo.fetch().then((state) => {
      const online = !!state.isConnected && state.isInternetReachable !== false;
      setIsOnline(online);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!isOnline) return;
    fetch(`${API_BASE}/appointments/locations/`)
      .then((res) => res.json())
      .then((data) => setLocations(data.locations || []))
      .catch((err) => console.error('Error fetching locations:', err));
  }, [isOnline]);

  useEffect(() => {
    if (!isOnline || !selectedLocation) return;
    fetch(
      `${API_BASE}/appointments/available-dates/?year=${year}&month=${month}&location=${selectedLocation}`
    )
      .then((res) => res.json())
      .then((data) => setAvailableDates(data.available_dates || []))
      .catch((err) => console.error('Error fetching available dates:', err));
  }, [year, month, selectedLocation, isOnline]);

  useEffect(() => {
    // Auto-complete tasks based on current state
    setTasks((prev) =>
      prev.map((t) => {
        if (t.id === 'location') return { ...t, done: !!selectedLocation };
        if (t.id === 'date') return { ...t, done: !!selectedDate };
        if (t.id === 'slot') return { ...t, done: !!selectedSlot };
        if (t.id === 'info') return { ...t, done: !!name && !!email && !!phone }; // Update info task condition
        return t;
      })
    );
  }, [selectedLocation, selectedDate, selectedSlot, name, email, phone]); // Add name to dependencies

  const fetchSlotsForDate = (dateStr) => {
    setSelectedDate(dateStr);
    if (!isOnline) {
      Alert.alert('Sem ligação', 'Está offline. Ligue-se ao Wi‑Fi.');
      return;
    }
    fetch(
      `${API_BASE}/appointments/available-slots/?date=${dateStr}&location=${selectedLocation}`
    )
      .then((res) => res.json())
      .then((data) => setSlots(data.available_slots || []))
      .catch((err) => console.error('Error fetching slots:', err));
  };

  const bookAppointment = () => {
    if (!selectedDate || !selectedSlot) return Alert.alert('Please select a date and a slot');
    if (!name || !email || !phone) return Alert.alert('Please fill in name, email and phone'); // Update alert message
    if (!isOnline) return Alert.alert('Sem ligação', 'Está offline. Ligue-se ao Wi‑Fi.');

    const payload = {
      name, // Add name to payload
      email,
      phone_number: phone,
      date: selectedDate,
      start_time: selectedSlot.start_time,
      end_time: selectedSlot.end_time,
      location: selectedLocation,
    };

    fetch(`${API_BASE}/appointments/book-appointment/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.message) {
          Alert.alert('Success', data.message);
          setSelectedSlot(null);
          setEmail('');
          setPhone('');
          setName(''); // Clear name after booking
          setTasks((prev) => prev.map((t) => (t.id === 'book' ? { ...t, done: true } : t)));
        } else {
          Alert.alert('Error', data.error || 'Unknown error');
        }
      })
      .catch((err) => {
        console.error('Error booking appointment:', err);
        Alert.alert('Error', 'Failed to book appointment');
      });
  };

  const renderTasks = () => {
    const completed = tasks.filter((t) => t.done).length;
    return (
      <View style={styles.tasksBox}>
        <Text style={styles.tasksTitle}>Tasks ({completed}/{tasks.length})</Text>
        {tasks.map((t) => (
          <View key={t.id} style={styles.taskItem}>
            <View style={[styles.checkbox, t.done && styles.checkboxDone]} />
            <Text style={[styles.taskLabel, t.done && styles.taskDone]}>{t.label}</Text>
          </View>
        ))}
      </View>
    );
  };

  const markedDates = useMemo(() => {
    const marks = {};
    (availableDates || []).forEach((d) => {
      marks[d] = { marked: true, dotColor: '#16a34a' };
    });
    if (selectedDate) {
      marks[selectedDate] = {
        ...(marks[selectedDate] || {}),
        selected: true,
        selectedColor: '#bfdbfe',
      };
    }
    return marks;
  }, [availableDates, selectedDate]);

  if (showIntro) {
    return (
      <View style={styles.introContainer}>
        <Text style={styles.introTitle}>Welcome to Osteopath Booking</Text>
        <Text style={styles.introText}>Meet Your Doctor</Text>
        <Image
          source={{ uri: 'https://via.placeholder.com/150' }} // Replace with actual doctor image
          style={styles.doctorImage}
        />
        <Text style={styles.doctorName}>Dr. John Doe</Text>
        <Text style={styles.doctorSpecialty}>Specialty: Osteopathy</Text>
        <Text style={styles.doctorDescription}>
          Dr. John Doe is a highly experienced osteopath with a passion for helping patients achieve optimal health and well-being. He specializes in treating musculoskeletal pain, improving mobility, and promoting overall body balance.
        </Text>
        {renderTasks()}
        <TouchableOpacity style={styles.startBtn} onPress={() => setShowIntro(false)}>
          <Text style={styles.startBtnText}>Get Started</Text>
        </TouchableOpacity>
        <StatusBar style="auto" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Osteopath Booking</Text>
      {!isOnline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>Sem internet: verifique a ligação Wi‑Fi</Text>
        </View>
      )}
      {renderTasks()}

      <Text style={styles.sectionTitle}>Select a Location</Text>
      <FlatList
        data={locations}
        keyExtractor={(item) => item.id.toString()}
        horizontal
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.locationBtn,
              selectedLocation === item.id && styles.locationBtnSelected,
            ]}
            onPress={() => setSelectedLocation(item.id)}
          >
            <Text style={styles.locationText}>{item.name}</Text>
          </TouchableOpacity>
        )}
        style={{ maxHeight: 60 }}
      />

      {selectedLocation && (
        <View>
          <Text style={styles.sectionTitle}>Calendar</Text>
          <Calendar
            minDate={todayStr}
            markedDates={markedDates}
            enableSwipeMonths={true}
            hideExtraDays={false}
            onDayPress={(day) => {
              const { dateString } = day;
              setSelectedDate(dateString);
              fetchSlotsForDate(dateString);
            }}
            onMonthChange={(m) => {
              setYear(m.year);
              setMonth(m.month);
            }}
          />
        </View>
      )}

      {selectedDate && (
        <View>
          <Text style={styles.sectionTitle}>Slots on {selectedDate}</Text>
          <FlatList
            data={slots}
            keyExtractor={(item, idx) => `${item.start_time}-${idx}`}
            horizontal
            renderItem={({ item }) => (
              <TouchableOpacity
                style={[styles.slotBtn, selectedSlot?.start_time === item.start_time && styles.slotBtnSelected]}
                onPress={() => setSelectedSlot(item)}
              >
                <Text style={styles.slotText}>{item.start_time}</Text>
              </TouchableOpacity>
            )}
            style={{ maxHeight: 60 }}
          />

          <View style={styles.form}>
            <TextInput
              placeholder="Name"
              value={name}
              onChangeText={setName}
              style={styles.input}
            />
            <TextInput
              placeholder="Email"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              style={styles.input}
            />
            <TextInput
              placeholder="Phone"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              style={styles.input}
            />
            <TouchableOpacity style={styles.bookBtn} onPress={bookAppointment}>
              <Text style={styles.bookBtnText}>Book Appointment</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', paddingTop: 40, paddingHorizontal: 16 },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  offlineBanner: { backgroundColor: '#fee2e2', borderColor: '#ef4444', borderWidth: 1, padding: 8, borderRadius: 6, marginBottom: 8 },
  offlineText: { color: '#b91c1c', fontWeight: '600' },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  navBtn: { backgroundColor: '#2563eb', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6 },
  navBtnText: { color: '#fff', fontWeight: '600' },
  monthText: { fontSize: 16, fontWeight: '600' },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginTop: 12, marginBottom: 8 },
  locationBtn: {
    backgroundColor: '#e5e7eb',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  locationBtnSelected: { backgroundColor: '#a5b4fc' },
  locationText: { fontSize: 14 },
  dateBtn: { backgroundColor: '#e5e7eb', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6, marginRight: 8 },
  dateBtnSelected: { backgroundColor: '#bfdbfe' },
  dateText: { fontSize: 14 },
  slotBtn: { backgroundColor: '#e5e7eb', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6, marginRight: 8 },
  slotBtnSelected: { backgroundColor: '#86efac' },
  slotText: { fontSize: 14 },
  form: { marginTop: 16 },
  input: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 6, padding: 10, marginBottom: 8 },
  bookBtn: { backgroundColor: '#16a34a', paddingVertical: 10, borderRadius: 6, alignItems: 'center' },
  bookBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  // Intro styles
  introContainer: { flex: 1, backgroundColor: '#fff', paddingTop: 60, paddingHorizontal: 20, alignItems: 'center' },
  introTitle: { fontSize: 24, fontWeight: '800', marginBottom: 8 },
  introText: { fontSize: 18, marginBottom: 12, textAlign: 'center' },
  doctorImage: { width: 150, height: 150, borderRadius: 75, marginBottom: 12 },
  doctorName: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
  doctorSpecialty: { fontSize: 16, color: '#555', marginBottom: 8 },
  doctorDescription: { fontSize: 14, textAlign: 'center', marginBottom: 20, color: '#777' },
  tasksBox: { backgroundColor: '#f3f4f6', borderRadius: 8, padding: 12, marginBottom: 16, width: '100%' },
  tasksTitle: { fontSize: 16, fontWeight: '700', marginBottom: 8 },
  taskItem: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  checkbox: { width: 16, height: 16, borderWidth: 2, borderColor: '#9ca3af', borderRadius: 4, marginRight: 8, backgroundColor: '#fff' },
  checkboxDone: { backgroundColor: '#22c55e', borderColor: '#22c55e' },
  taskLabel: { fontSize: 14, color: '#111827' },
  taskDone: { color: '#16a34a', textDecorationLine: 'line-through' },
  startBtn: { backgroundColor: '#2563eb', paddingVertical: 12, borderRadius: 8, alignItems: 'center', width: '100%' },
  startBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
