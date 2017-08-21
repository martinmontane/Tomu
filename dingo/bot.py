#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
from discord.ext import commands
from django.conf import settings
from .models import *
from django.contrib.auth.models import User
import discord
import asyncio
import os
import traceback
import importlib
import atexit

class DingoB(commands.Bot):
    def __init__(self):
        #print("{} bot".format(os.getpid()))
        self.config=settings.BOTCONFIG

        prefix=settings.BOTCONFIG['bot']['prefixes']
        description = settings.BOTCONFIG["strings"]["description"]

        super().__init__(command_prefix=prefix, description=description)

        self.announcements = settings.BOTCONFIG['server']['announces'].lower()
        self.output =  settings.BOTCONFIG['server']['output'].lower()

        #preparing the variables that will be replaced by the roles and colors
        self.botrole = settings.BOTCONFIG['server']['bot-role']
        self.adminrole = settings.BOTCONFIG['server']['admin-role']
        self.botcolor = discord.Colour(settings.BOTCONFIG['server']['bot-color'])
        self.admincolor = discord.Colour(settings.BOTCONFIG['server']['admin-color'])

        self.commodule = settings.BOTCONFIG['main']['botmodule']

        #create the events
        self.on_ready = self.event(self.on_ready)
        self.on_command_error = self.event(self.on_command_error)

  
        self.all_ready = False

        #serching for the plugins
        plugins=[]

        for i in settings.INSTALLED_APPS:
            if 'django' in i:
                continue
            check = importlib.util.find_spec(".{}".format(self.commodule), package=i)
            if check is not None:
                plugins.append("{}.{}".format(i, self.commodule))

        self.failedplugins = []

        #loading the plugins
        for plugin in plugins:
            try:
                self.load_extension(plugin)
            except Exception as e:
                print('Error on {}:\n {}: {}'.format(plugin, type(e).__name__, e))
                traceback.print_exc()
                self.failedplugins.append([plugin, type(e).__name__, e])


    async def on_command_error(self, error, context):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            pass
        elif isinstance(error, discord.ext.commands.errors.CheckFailure):
            await self.send_message(context.message.channel, "{} you don't have permission to use this command".format(context.message.author.mention))
        elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            formatter = commands.formatter.HelpFormatter()
            await self.send_message(context.message.channel, "{} you are missing required arguments.\n{}".format(context.message.author.mention, formatter.format_help_for(context, context.command)[0]))
        elif isinstance(error, discord.ext.commands.errors.BadArgument):
            formatter = commands.formatter.HelpFormatter()
            await self.send_message(context.message.channel, "{} you miss entered an argument in the `{}` command.\n{}".format(context.message.author.mention, context.command.name, formatter.format_help_for(context, context.command)[0]))
        elif context.command:
            await self.send_message(context.message.channel, "An error occured while processing the `{}` command.".format(context.command.name))
            print('Ignoring exception in command {}'.format(context.command))
            traceback.print_exception(type(error), error, error.__traceback__)

    async def on_ready(self):
        if self.all_ready:
            return

        #print("{} is working".format(os.getpid()))
        #print bot info
        print("-------")
        print("Logged: "+ str(self.is_logged_in))
        print("UserName: "+self.user.name)
        print("Description: "+ self.description)
        print("ID: "+ self.user.id)
        print("-------")

        #get the working server. This self.bot would work better with only one server
        for server in self.servers:
            self.server = server

        #create the defult roles
        br = discord.utils.get(server.me.roles, name=self.botrole)
        if br:
            self.botrole = br
        else:
            self.botrole = await self.create_role(server, name=self.botrole, permissions=discord.Permissions().all(), colour=self.botcolor, hoist=True, mentionable=False)
            await self.add_roles(self.user, self.botrole)

        ar = discord.utils.get(server.roles, name=self.adminrole)
        if ar:
            self.adminrole = ar
        else:
            self.adminrole = await self.create_role(server, name=self.adminrole, permissions=discord.Permissions.all(), colour=admincolor, hoist=True, mentionable=True)

        #Default channels
            #announcements
        an=discord.utils.get(server.channels, name=self.announcements)
        if not an:
            everyone_perms = discord.PermissionOverwrite(send_messages=False, send_tts_messages=False)
            my_perms = discord.PermissionOverwrite(send_messages=True, send_tts_messages=True)

            await self.edit_channel_permissions(server.default_channel, server.default_role, everyone_perms)
            await self.edit_channel_permissions(server.default_channel, self.botrole, my_perms)
            await self.edit_channel(server.default_channel, name=self.announcements)

        self.announcements = server.default_channel
        await self.move_channel(self.announcements, 0)
            #output
        op = discord.utils.get(server.channels, name=self.output)
        if not op:
            everyone_perms = discord.PermissionOverwrite(read_messages=False)
            bot_perms = discord.PermissionOverwrite(read_messages=True)
            admin_perms = discord.PermissionOverwrite(read_messages=True)

            everyone = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
            mine = discord.ChannelPermissions(target=self.botrole, overwrite=bot_perms)
            adminperm = discord.ChannelPermissions(target=self.adminrole, overwrite=admin_perms)

            op = await self.create_channel(server, self.output, everyone, mine, adminperm)
        self.output = op
        await self.move_channel(self.output, 1)

        self.all_ready=True

        msg=""
        if len(self.failedplugins) != 0:
            msg += "\n\nFailed to load:\n"
            for f in self.failedplugins:
                msg += "\n{}: `{}: {}`".format(*f)
            await self.send_message(self.output, msg)

        await self.send_message(self.output, "{} is back".format(self.user.name))


    def begin(self):
        if os.path.isfile('lock'):
            #print("{} doesn't work".format(os.getpid()))
            return
        lock = open('lock', 'w')
        if not os.path.isfile("spam"):
            with open("spam", "w") as f:
                f.write("{}")
        self.run(self.config['main']['token'])



@atexit.register
def close():
    os.remove('lock')