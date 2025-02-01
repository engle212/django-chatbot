import React, { useEffect, useState } from "react";
import axios from "axios";
import { styled, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import MuiAppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Stack from '@mui/material/Stack';
import BottomNavigation from '@mui/material/BottomNavigation';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid2';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';

const drawerWidth = 360;
const BASE_URL = "http://127.0.0.1:8000";
const API_URL = BASE_URL + "/chat/";

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme }) => ({
    flexGrow: 1,
    padding: theme.spacing(3),
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginLeft: `-${drawerWidth}px`,
    variants: [
      {
        props: ({ open }) => open,
        style: {
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.easeOut,
            duration: theme.transitions.duration.enteringScreen,
          }),
          marginLeft: 0,
        },
      },
    ],
  }),
);

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme }) => ({
  transition: theme.transitions.create(['margin', 'width'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  variants: [
    {
      props: ({ open }) => open,
      style: {
        width: `calc(100% - ${drawerWidth}px)`,
        marginLeft: `${drawerWidth}px`,
        transition: theme.transitions.create(['margin', 'width'], {
          easing: theme.transitions.easing.easeOut,
          duration: theme.transitions.duration.enteringScreen,
        }),
      },
    },
  ],
}));

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: 'flex-end',
}));

function PersistentDrawerLeft({context, submitHandler, changeHandler}) {
  const theme = useTheme();
  const [open, setOpen] = React.useState(false);

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" open={open}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={[
              {
                mr: 2,
              },
              open && { display: 'none' },
            ]}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {context.title}
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="persistent"
        anchor="left"
        open={open}>
        <DrawerHeader>
          
          <Button onClick={handleDrawerClose} variant="text">
            Conversations
            {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
          </Button>
        </DrawerHeader>
        <Divider />
        <List>
          {context.convos.map((convo, idx) => (
            <ListItem key={idx} id={convo[0]} disablePadding>
              <ListItemButton href={BASE_URL + "/swap/" + convo[0]}>
                <ListItemText primary={convo[1]}/>
              </ListItemButton>
            </ListItem>
          ))}
        </List>

      </Drawer>
      <Main open={open}>
        <DrawerHeader />
        {/* Main app content */}
        <Container maxWidth="sm" sx={{ height: '100vh', display: 'flex' }}>
          <Stack direction="column-reverse" spacing={2} sx={{flexGrow: 1, height: '100%', width: '100%', alignItems: "stretch", justifyContent: "flex-start"}}>
            <Box sx={{flexGrow: 0, height: '10vh'}}/>

            {context.messages.map((msg, idx) => (
              <Message isUser={msg[0]} text={msg[1]} />
            ))}

            <Message isUser={1} text={"Hello, I am robot"} />
            <Message isUser={0} text={"Helloooooo"} />
          </Stack>
        </Container>
        <BottomNavigation sx={{position: 'fixed', bottom: 0, left: 0, right: 0, paddingBottom: 10, display: 'flex'}}>
          <Box component="form" onSubmit={submitHandler} sx={{ display: "contents" }} action="." method="POST">
            <Container maxWidth="md" sx={{display: 'flex', height: '100%'}}>
              <Grid container spacing={2} sx={{flexGrow: 1, paddingRight: 5}}>
                <Grid size={11}>
                  <TextField fullWidth name="text" onChange={changeHandler}/>
                </Grid>
                <Grid size={1}>
                  <Button type="submit" variant="contained" sx={{flexGrow: 1, height: "100%"}}><ChevronRightIcon/></Button>
                </Grid>
              </Grid>
            </Container>
          </Box>
        </BottomNavigation>
      </Main>
    </Box>
  );
}

export function App() {
  const [context, setContext] = useState(null);
  const [text, setText] = useState({"text": "hey"});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get(API_URL)
      .then((response) => {
        setContext(response.data);
        setLoading(false);
        console.log(response.data);
      })
      .catch((error) => {
        console.error("Error fetching context:", error);
        setLoading(false);
      });
  }, []);

  const handleChange = event => {
    setText({"text": event.target.value});
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    axios.post(API_URL, text)
      .then((response) => {
        console.log(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  if (loading) return <p>Loading...</p>;

  return (
    <PersistentDrawerLeft context={context} submitHandler={handleSubmit} changeHandler={handleChange}/>
    /*<div>
      {/* Use Persistent drawer for sidebar }
      <h1>{context.title}</h1>
      <h2>Conversation ID: {context.convo_id}</h2>

      <h3>Messages:</h3>
      <ul>
        {context.messages.map((msg, idx) => (
          <li key={idx}>
            <strong>{msg.sender}:</strong> {msg.text}
          </li>
        ))}
      </ul>
      <h3>Conversations</h3>
      {context.convos.map((convo, idx) => (
        <div>
          <ConvoButton id={convo[0]} filename={convo[1]} summary={convo[2]} />
          <Button variant="outlined">Hello world</Button>
        </div>
      ))}
    </div>*/
  );
}
export default App;

function Message({isUser, text}) {
  if (isUser === 0) {
    return (
      <Grid container sx={{flexGrow: 0}}>
        <Grid size={4}>
        </Grid>
        <Grid size={8}>
          <Paper variant="outlined" sx={{padding: 3}}>{text}</Paper>
        </Grid>
      </Grid>
    );
  } else {
    return (
      <Grid container sx={{flexGrow: 0}}>
        <Grid size={8}>
          <Paper variant="elevation" sx={{padding: 3}}>{text}</Paper>
        </Grid>
        <Grid size={4}>
        </Grid>
      </Grid>
    );
  }
};