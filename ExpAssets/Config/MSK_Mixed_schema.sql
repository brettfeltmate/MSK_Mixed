

CREATE TABLE participants (
	id integer primary key autoincrement not null,
	userhash text not null,
	gender text not null,
	age integer not null, 
	handedness text not null,
	created text not null
);

CREATE TABLE trials (
	id integer primary key autoincrement not null,
	participant_id integer not null references participants(id),
	practicing text not null,
	block_num integer not null,
	trial_num integer not null,
	isoa text not null,
	isi text not null,
	ttoa text not null,
	t1_difficulty text not null,
	t1_duration text not null,
	m1_duration text not null,
	t2_duration text not null,
	m2_duration text not null,
	t1_identity text not null,
	t2_identity text not null,
	t1_response text not null,
	t2_response text not null
);
