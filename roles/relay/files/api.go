package main

type PlayerDBResponse struct {
	Code    string       `json:"code"`
	Message string       `json:"message"`
	Data    PlayerDBData `json:"data"`
	Success bool         `json:"success"`
}

type PlayerDBData struct {
	Player PlayerDBPlayer `json:"player"`
}

type PlayerDBPlayer struct {
	Meta        PlayerDBPlayerMeta       `json:"meta"`
	Username    string                   `json:"username"`
	Id          string                   `json:"id"`
	RawID       string                   `json:"raw_id"`
	Avatar      string                   `json:"avatar"`
	SkinTexture string                   `json:"skin_texture"`
	Properties  []PlayerDBPlayerProperty `json:"properties"`
	NameHistory []string                 `json:"name_history"`
}

type PlayerDBPlayerMeta struct {
	CachedAt int `json:"cached_at"`
}

type PlayerDBPlayerProperty struct {
	Name      string `json:"name"`
	Value     string `json:"value"`
	Signature string `json:"signature"`
}
