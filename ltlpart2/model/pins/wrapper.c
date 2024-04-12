#include <assert.h>
#include <stdlib.h>
#include "loader.h"

#define _sizeof(a, b) (sizeof(a)/sizeof(b))

// callback into Python with arbitrary arguments
typedef void (*_wrapperCallback)(char *kind, int argc, void **argv);
_wrapperCallback _pyCallback;

void _wrapperInit(_wrapperCallback fn){
  // Set callback to return to Python.
  _pyCallback = fn;
}

StateLabelLongFn _stateLabelLong = NULL;
StateLabelAllFn _stateLabelAll = NULL;

int _wrapperGetStateLabelsLong(int *dst, int dmax, void *src){
  int n = 0;
  for(int i = 0; i < dmax; i++){
    if((*_stateLabelLong)(NULL, i, src)==0)
      continue;
    dst[n++] = i;
  }
  return n;
}

int _wrapperGetStateLabelsAll(int *dst, int dmax, void *src){
  int n = 0;
  (*_stateLabelAll)(NULL, src, dst);
  for(int i = 0; i < dmax; i++){
    if(dst[i]==0)
      continue;
    dst[n++] = i;
  }
  return n;
}

int _wrapperGetStateLabels(int *dst, int dmax, void *src){
  // Puts the index for all state labels for the state [src] in the
  //  [dmax]-length array [dst].
  // Returns the number of state labels.
  if(_stateLabelAll!=NULL)
    return _wrapperGetStateLabelsAll(dst, dmax, src);
  else if(_stateLabelLong!=NULL)
    return _wrapperGetStateLabelsLong(dst, dmax, src);

  return 0;
}

// Miscellaneous functions for loader use
void _wrapperSetActionCount(int i){
  void *args[] = {&i};
  (*_pyCallback)("setActionCount", _sizeof(args, void *), args);
}

void _wrapperSetActionLabel(int i){
  void *args[] = {&i};
  (*_pyCallback)("setActionLabel", _sizeof(args, void *), args);
}

// State functions
void lts_type_set_state_length(void *type, int length){
  // Set state length to [length].
  void *args[] = {&length};
  (*_pyCallback)("setStateLength", _sizeof(args, void *), args);
}

void lts_type_set_state_name(void *type, int i, char *name){
  // Set the name of state slot [i] to [name].
  void *args[] = {&i, name};
  (*_pyCallback)("setStateSlotName", _sizeof(args, void *), args);
}

void lts_type_set_state_typeno(void *type, int i, int tid){
  // Set the type of state slot [i] to the type identified by [tid].
}

void GBsetInitialState(void *model, int *initial){
  // Set the initial state to [initial].
  void *args[] = {initial};
  (*_pyCallback)("setInitialState", _sizeof(args, void *), args);
}

void GBsetNextStateShort(void *model, void (*fn)()){
}

void GBsetNextStateLong(void *model, void (*fn)()){
}

void GBsetNextStateAll(void *model, void (*fn)()){
  // Set the next-state function to [fn].
  (*_pyCallback)("setNextStatesFn", 1, (void *)&fn);
}

// State label functions
void lts_type_set_state_label_count(void *type, int n){
  // Set the amount of state labels to [n].
  void *args[] = {&n};
  (*_pyCallback)("setStateLabelCount", _sizeof(args, void *), args);
}

void lts_type_set_state_label_name(void *type, int i, char *name){
  // Set the name of state label [i] to [name].
  void *args[] = {&i, name};
  (*_pyCallback)("setStateLabelName", _sizeof(args, void *), args);
}

void lts_type_set_state_label_typeno(void *type, int i, int n){
  // Set the type of state label [i] to [n].
}

void GBsetStateLabelShort(void *model, void (*fn)()){
  // Set the state label evaluation function for short vectors to [fn].
}

void GBsetStateLabelLong(void *model, StateLabelLongFn fn){
  // Set the state label evaluation function for long vectors to [fn].
  _stateLabelLong = fn;
}

void GBsetStateLabelsAll(void *model, StateLabelAllFn fn){
  // Set the state label evaluation function to [fn].
  _stateLabelAll = fn;
}

void GBsetStateLabelInfo(void *model, struct Matrix *mtx){
  // Set state label dependency matrix to [mtx] (state labels x slots).
  void *args[] = {"guardTest", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

// Edge label functions
void lts_type_set_edge_label_count(void *type, int n){
  // Set the amount of edge labels to [n].
  void *args[] = {&n};
  (*_pyCallback)("setEdgeLabelCount", _sizeof(args, void *), args);
}

void lts_type_set_edge_label_name(void *type, int i, char *name){
  // Set the name of edge label [i] to [name].
  void *args[] = {&i, name};
  (*_pyCallback)("edgeLabels.#.setName", _sizeof(args, void *), args);
}

void lts_type_set_edge_label_type(void *type, int i, char *name){
  // Set the type of edge label [i] to the type identified by [name].
}

void lts_type_set_edge_label_typeno(void *type, int i, int tid){
  // Set the type of edge label [i] to the type identified by [tid].
  void *args[] = {&i, &tid};
  (*_pyCallback)("edgeLabels.#.setType", _sizeof(args, void *), args);
}

// Affect set functions
void GBsetDMInfoRead(void *model, struct Matrix *mtx){
  // Set read dependency matrix to [mtx] (actions x slots).
  void *args[] = {"actionRead", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetDMInfoMayWrite(void *model, struct Matrix *mtx){
  // Set write dependency matrix to [mtx] (actions x slots).
  void *args[] = {"actionMayWrite", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetDMInfoMustWrite(void *model, struct Matrix *mtx){
  // Set write dependency matrix to [mtx] (actions x slots).
  void *args[] = {"actionMustWrite", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetDMInfo(void *model, struct Matrix *mtx){
  // Set read/write dependency matrix to [mtx] (actions x slots).
  void *args[] = {"actionAccess", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

// Guard functions
void GBsetGuard(void *model, int aid, struct Guard *guard){
  // Set [guards] for an individual action [aid].
  void *args[] = {&aid, guard};
  (*_pyCallback)("setGuards", _sizeof(args, void *), args);
}

void GBsetGuardsInfo(void *model, struct Guard **guards){
  // Set [guards] for all actions.
  void *args[] = {guards};
  (*_pyCallback)("setGuardsAll", _sizeof(args, void *), args);
}

// Reduction information functions
void GBsetDoNotAccordInfo(void *model, struct Matrix *mtx){
  // Set do-not-accord matrix to [mtx] (actions x actions).
  void *args[] = {"noAccord", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetGuardNESInfo(void *model, struct Matrix *mtx){
  // Set guard NES matrix to [mtx] (state labels x actions).
  void *args[] = {"guardNES", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetGuardNDSInfo(void *model, struct Matrix *mtx){
  // Set guard NDS matrix to [mtx] (state labels x actions).
  void *args[] = {"guardNDS", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetCommutesInfo(void *model, struct Matrix *mtx){
  // Set commutation matrix to [mtx] (actions x actions).
  void *args[] = {"commute", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

void GBsetGuardCoEnabledInfo(void *model, struct Matrix *mtx){
  // Set guard co-enabled matrix to [mtx] (state labels x state labels).
  void *args[] = {"coenable", mtx};
  (*_pyCallback)("setMatrix", _sizeof(args, void *), args);
}

// Type functions
void lts_type_create(void){
}

int lts_type_add_type(void *type, char *name, void *ptr){
  // Add a new type with a given [name].
  static int tid = 0;
  void *args[] = {&tid, name};
  (*_pyCallback)("addType", _sizeof(args, void *), args);
  return tid++;
}

void lts_type_set_format(void *type, int tid, int n){
  void *args[] = {&tid, &n};
  (*_pyCallback)("types.#.setFormat", _sizeof(args, void *), args);
}

void lts_type_validate(void *type){
}

void GBsetLTStype(void *model, void *type){
}

void GBchunkPut(void *model, int tid, struct Chunk chunk){
  // Add a chunk string [chunk] to the type identified by [tid].
  assert(chunk.str[chunk.len]=='\0');
  void *args[] = {&tid, chunk.str};
  (*_pyCallback)("types.#.addChunk", _sizeof(args, void *), args);
}

void pins_chunk_put(void *model, int tid, struct Chunk chunk){
  GBchunkPut(model, tid, chunk);
}

// Matrix functions
void dm_create(struct Matrix *mtx, int n, int m){
  mtx->n = n;
  mtx->m = m;
  mtx->data = calloc(n * m, 1);
}

void dm_set(struct Matrix *mtx, int i, int j){
  mtx->data[(mtx->m * i) + j] = 1;
}
